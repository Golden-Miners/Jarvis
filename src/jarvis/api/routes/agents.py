"""Agents routes."""
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select

from jarvis.api.auth import UserInDB, require_viewer
from jarvis.api.schemas import AgentStatusResponse
from jarvis.api.sse import broadcast_agent_health
from jarvis.db.models import AgentRunModel
from jarvis.db.session import make_engine

router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("/status", response_model=list[AgentStatusResponse])
async def agents_status(
    cycle_id: str | None = None,
    agent: str | None = None,
    limit: int = Query(100, ge=1, le=500),
    current_user: UserInDB = Depends(require_viewer),  # noqa: B008
) -> list[AgentStatusResponse]:
    """Get agent run statuses."""
    engine = make_engine()
    with Session(engine) as session:
        stmt = select(AgentRunModel)
        if cycle_id:
            stmt = stmt.where(AgentRunModel.cycle_id == cycle_id)
        if agent:
            stmt = stmt.where(AgentRunModel.agent == agent)
        stmt = stmt.order_by(AgentRunModel.created_at.desc()).limit(limit)  # type: ignore
        results = list(session.exec(stmt).all())

    # Group by agent and get latest per agent
    latest_by_agent = {}
    for run in results:
        if run.agent not in latest_by_agent:
            latest_by_agent[run.agent] = run

    return [
        AgentStatusResponse(
            agent=run.agent,
            symbol=run.symbol,
            last_run=run.created_at.isoformat() if run.created_at else "",
            latency_ms=run.latency_ms or 0,
            status=run.status,  # type: ignore
            error=run.error_message,
        )
        for run in latest_by_agent.values()
    ]


# Internal function for graph to log agent runs
async def log_agent_run(
    *,
    id: str,
    cycle_id: str,
    agent: str,
    symbol: str | None,
    status: str,
    error_code: str | None = None,
    error_message: str | None = None,
    latency_ms: int | None = None,
    llm_tokens_in: int | None = None,
    llm_tokens_out: int | None = None,
) -> AgentRunModel:
    """Log an agent run (called from graph)."""
    engine = make_engine()
    with Session(engine) as session:
        run = AgentRunModel(
            id=id,
            cycle_id=cycle_id,
            agent=agent,
            symbol=symbol,
            status=status,
            error_code=error_code,
            error_message=error_message,
            latency_ms=latency_ms,
            llm_tokens_in=llm_tokens_in,
            llm_tokens_out=llm_tokens_out,
            created_at=datetime.now(UTC),
        )
        session.add(run)
        session.commit()
        session.refresh(run)

    # Broadcast SSE event
    await broadcast_agent_health({
        "agent": agent,
        "symbol": symbol,
        "status": status,
        "latency_ms": latency_ms,
        "error": error_message,
        "timestamp": datetime.now(UTC).isoformat(),
    })

    return run