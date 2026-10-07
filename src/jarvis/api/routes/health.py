"""Health and root routes."""
import traceback
from typing import Literal

from fastapi import APIRouter
from sqlmodel import text

from jarvis.api.schemas import HealthResponse
from jarvis.db.session import make_engine

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Liveness + adapter health check."""
    db_status: Literal["healthy", "degraded", "unhealthy"] = "unhealthy"
    try:
        engine = make_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception:
        traceback.print_exc()

    adapters: dict[str, Literal["healthy", "degraded", "unhealthy", "unknown"]] = {
        "database": db_status,
        "mt5": "unknown",
        "anthropic": "unknown",
        "timesfm": "unknown",
    }

    all_healthy = all(v == "healthy" for v in adapters.values())
    overall: Literal["healthy", "degraded", "unhealthy"] = "healthy" if all_healthy else "degraded"

    return HealthResponse(status=overall, adapters=adapters)
