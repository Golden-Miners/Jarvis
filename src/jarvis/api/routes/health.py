"""Health and root routes."""
import traceback

from fastapi import APIRouter
from sqlmodel import text

from jarvis.api.schemas import HealthResponse
from jarvis.db.session import make_engine

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Liveness + adapter health check."""
    db_status = "unhealthy"
    try:
        engine = make_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception:
        traceback.print_exc()

    adapters: dict[str, str] = {
        "database": db_status,
        "mt5": "unknown",
        "anthropic": "unknown",
        "timesfm": "unknown",
    }

    overall = "healthy" if all(v == "healthy" for v in adapters.values()) else "degraded"

    return HealthResponse(status=overall, adapters=adapters)
