"""Authentication and authorization for FastAPI backend."""
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Literal

from fastapi import Depends, HTTPException, Request, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, ConfigDict
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlmodel import Session, select

from jarvis.db.models import UserModel
from jarvis.db.repositories import audit_log
from jarvis.db.session import make_engine


class AuthSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    jwt_secret: str = "dev-secret-change-in-production-min-32-chars"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    cookie_domain: str = "localhost"
    cookie_secure: bool = False  # True in production with HTTPS


settings = AuthSettings()

# Use argon2 as primary, keep bcrypt for verifying existing hashes
pwd_context = CryptContext(schemes=["argon2", "bcrypt"], deprecated="auto")
security = HTTPBearer(auto_error=False)

Role = Literal["OWNER", "VIEWER", "SYSTEM"]


class TokenData(BaseModel):
    model_config = ConfigDict(extra="forbid")
    sub: str
    role: Role
    exp: int
    type: Literal["access", "refresh"]


class UserInDB(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)
    id: str
    username: str
    password_hash: str
    role: Role
    active: bool


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        print(f"[AUTH ERROR] verify_password failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def create_access_token(username: str, role: Role) -> str:
    expire = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode = TokenData(sub=username, role=role, exp=int(expire.timestamp()), type="access")
    return jwt.encode(to_encode.model_dump(), settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_refresh_token(username: str, role: Role) -> str:
    expire = datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days)
    to_encode = TokenData(sub=username, role=role, exp=int(expire.timestamp()), type="refresh")
    return jwt.encode(to_encode.model_dump(), settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> TokenData:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        return TokenData(**payload)
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e


def get_user_by_username(username: str) -> UserInDB | None:
    engine = make_engine()
    with Session(engine) as session:
        user = session.exec(select(UserModel).where(UserModel.username == username)).first()
        if user:
            return UserInDB.model_validate(user)
    return None


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),  # noqa: B008
) -> UserInDB:
    """Get current user from JWT token."""
    # Try to get token from Authorization header
    token = credentials.credentials if credentials else None

    # Fallback to cookie
    if not token:
        token = request.cookies.get("access_token")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token_data = decode_token(token)

    if token_data.type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    user = get_user_by_username(token_data.sub)
    if not user or not user.active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    return user


request_counts: dict[str, list[datetime]] = {}


def rate_limit_check(request: Request) -> None:
    client_ip = request.client.host if request.client else "unknown"
    now = datetime.now(UTC)

    cutoff = now.timestamp() - 60
    counts = request_counts.get(client_ip, [])
    request_counts[client_ip] = [t for t in counts if t.timestamp() > cutoff]

    if request.url.path.startswith("/api/v1/cycles/run"):
        limit = 1
    else:
        limit = 60

    if len(request_counts.get(client_ip, [])) >= limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
            headers={"Retry-After": "60"}
        )

    request_counts.setdefault(client_ip, []).append(now)



...

def require_role(*allowed_roles: Role) -> Callable[[Request], UserInDB]:
    """Dependency factory for role-based access control."""

    def checker(request: Request, user: UserInDB = Depends(get_current_user)) -> UserInDB:  # noqa: B008
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        rate_limit_check(request)
        return user

    return checker


# Convenience dependencies
require_owner = require_role("OWNER")
require_viewer = require_role("OWNER", "VIEWER")


def set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="strict",
        max_age=settings.access_token_expire_minutes * 60,
        domain=settings.cookie_domain if settings.cookie_domain != "localhost" else None,
        path="/",
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="strict",
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60,
        domain=settings.cookie_domain if settings.cookie_domain != "localhost" else None,
        path="/",
    )


def clear_auth_cookies(response: Response) -> None:
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/")


async def log_audit(
    actor: str,
    action: str,
    entity: str | None = None,
    entity_id: str | None = None,
    payload: str | None = None,
) -> None:
    """Log an audit entry."""
    engine = make_engine()
    with Session(engine) as session:
        import uuid
        audit_log.append_audit_log(
            session,
            id=uuid.uuid4().hex,
            ts=datetime.now(UTC),
            actor=actor,
            action=action,
            entity=entity,
            entity_id=entity_id,
            payload=payload,
        )