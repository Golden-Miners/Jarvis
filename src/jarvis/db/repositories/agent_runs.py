"""Agent run persistence."""
# mypy: ignore-errors
from datetime import datetime

from sqlalchemy import select
from sqlmodel import Session

from jarvis.db.models import AgentRunModel


def upsert_agent_run(
    session: Session,
    *,
    id: str,
    cycle_id: str,
    agent: str,
    symbol: str | None,
    status: str,
    error_code: str | None,
    error_message: str | None,
    latency_ms: int | None,
    llm_tokens_in: int | None,
    llm_tokens_out: int | None,
    created_at: datetime,
) -> AgentRunModel:
    """Insert or update an agent run record."""
    row = AgentRunModel(
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
        created_at=created_at,
    )
    merged = session.merge(row)
    session.commit()
    return merged


def get_agent_run(session: Session, id: str) -> AgentRunModel | None:
    """Fetch an agent run by id."""
    return session.get(AgentRunModel, id)


def list_agent_runs(
    session: Session,
    cycle_id: str | None = None,
    agent: str | None = None,
    limit: int = 100,
) -> list[AgentRunModel]:
    """List agent runs, optionally filtered."""
    stmt = select(AgentRunModel)
    if cycle_id:
        stmt = stmt.where(AgentRunModel.cycle_id == cycle_id)
    if agent:
        stmt = stmt.where(AgentRunModel.agent == agent)
    stmt = stmt.order_by(AgentRunModel.created_at.desc()).limit(limit)
    return list(session.exec(stmt).scalars().all())  # type: ignore