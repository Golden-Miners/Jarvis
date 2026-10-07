"""Signal verdict persistence (per-agent evidence)."""
# mypy: ignore-errors

from sqlalchemy import select
from sqlmodel import Session

from jarvis.db.models import SignalVerdictModel


def upsert_signal_verdict(
    session: Session,
    *,
    id: str,
    signal_id: str,
    agent: str,
    verdict: str,
    weight: float,
    contribution: float,
    note: str | None,
) -> SignalVerdictModel:
    """Insert or update a signal verdict."""
    row = SignalVerdictModel(
        id=id,
        signal_id=signal_id,
        agent=agent,
        verdict=verdict,
        weight=weight,
        contribution=contribution,
        note=note,
    )
    merged = session.merge(row)
    session.commit()
    return merged


def get_signal_verdicts(session: Session, signal_id: str) -> list[SignalVerdictModel]:
    """Fetch all verdicts for a signal."""
    stmt = select(SignalVerdictModel).where(SignalVerdictModel.signal_id == signal_id)
    return list(session.exec(stmt).scalars().all())  # type: ignore


def list_signal_verdicts(session: Session, limit: int = 100) -> list[SignalVerdictModel]:
    """List all signal verdicts."""
    stmt = select(SignalVerdictModel).limit(limit)
    return list(session.exec(stmt).scalars().all())  # type: ignore