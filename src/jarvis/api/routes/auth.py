"""Auth routes."""
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, ConfigDict, Field
from sqlmodel import Session, select

from jarvis.api.auth import (
    UserInDB,
    create_access_token,
    create_refresh_token,
    get_current_user,
    hash_password,
    log_audit,
    set_auth_cookies,
    verify_password,
)
from jarvis.db.models import UserModel
from jarvis.db.session import make_engine

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    username: str
    role: str


failed_login_attempts: dict[str, list[datetime]] = {}

@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    response: Response,
):
    """Login with username/password, returns JWT tokens in cookies."""
    now = datetime.now(UTC)
    cutoff = now.timestamp() - (15 * 60)  # 15 minutes
    attempts = failed_login_attempts.get(request.username, [])
    recent_attempts = [t for t in attempts if t.timestamp() > cutoff]
    failed_login_attempts[request.username] = recent_attempts
    
    if len(recent_attempts) >= 5:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed login attempts. Please try again in 15 minutes.",
        )

    engine = make_engine()
    with Session(engine) as session:
        user = session.exec(select(UserModel).where(UserModel.username == request.username)).first()
        if not user or not user.active:
            failed_login_attempts.setdefault(request.username, []).append(now)
            await log_audit(
                actor=request.username,
                action="login_failed",
                entity="user",
                entity_id="unknown",
                payload=f"invalid username: {request.username}",
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )
        if not verify_password(request.password, user.password_hash):
            failed_login_attempts.setdefault(request.username, []).append(now)
            await log_audit(
                actor=request.username,
                action="login_failed",
                entity="user",
                entity_id=user.id,
                payload=f"failed login for {request.username}",
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )

        access_token = create_access_token(user.username, user.role)  # type: ignore
        refresh_token = create_refresh_token(user.username, user.role)  # type: ignore

        set_auth_cookies(response, access_token, refresh_token)

        await log_audit(
            actor=user.username,
            action="login",
            entity="user",
            entity_id=user.id,
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=15 * 60,  # 15 minutes
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    response: Response,
    refresh_token: str | None = None,
):
    """Refresh access token using refresh token from cookie."""
    if not refresh_token:
        refresh_token = response.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No refresh token",
        )

    from jarvis.api.auth import decode_token, get_user_by_username
    try:
        token_data = decode_token(refresh_token)
        if token_data.type != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid refresh token") from e

    user = get_user_by_username(token_data.sub)
    if not user or not user.active:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    access_token = create_access_token(user.username, user.role)  # type: ignore
    new_refresh_token = create_refresh_token(user.username, user.role)  # type: ignore

    set_auth_cookies(response, access_token, new_refresh_token)

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        expires_in=15 * 60,
    )


@router.post("/logout")
async def logout(response: Response):
    """Logout and clear cookies."""
    from jarvis.api.auth import clear_auth_cookies
    clear_auth_cookies(response)
    return {"message": "Logged out"}


@router.get("/me", response_model=UserResponse)
async def me(current_user: UserInDB = Depends(get_current_user)):  # noqa: B008
    """Get current user info."""
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        role=current_user.role,
    )


# Admin: create user (first user setup)
class CreateUserRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    username: str = Field(..., min_length=3)
    password: str = Field(..., min_length=12)
    role: str = Field(default="OWNER", pattern="^(OWNER|VIEWER)$")


@router.post("/users", response_model=UserResponse)
async def create_user(
    request: CreateUserRequest,
    current_user: UserInDB = Depends(get_current_user),  # noqa: B008
):
    """Create a new user (OWNER only)."""
    if current_user.role != "OWNER":
        raise HTTPException(status_code=403, detail="Only OWNER can create users")

    engine = make_engine()
    with Session(engine) as session:
        stmt = select(UserModel).where(UserModel.username == request.username)
        existing = session.exec(stmt).first()
        if existing:
            raise HTTPException(status_code=400, detail="Username already exists")

        user = UserModel(
            id=datetime.now(UTC).isoformat().replace(":", "").replace("-", "")[:24],
            username=request.username,
            password_hash=hash_password(request.password),
            role=request.role,
            active=1,
            created_at=datetime.now(UTC),
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        await log_audit(
            actor=current_user.username,
            action="create_user",
            entity="user",
            entity_id=user.id,
            payload=f"created user {request.username} with role {request.role}",
        )

        return UserResponse(id=user.id, username=user.username, role=user.role)