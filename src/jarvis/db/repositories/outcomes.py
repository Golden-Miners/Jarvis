"""Outcome persistence (Coulson): one outcome row per signal."""
# mypy: ignore-errors
from sqlalchemy import select
from sqlmodel import Session

from jarvis.db.models import OutcomeModel, SignalModel
from jarvis.schemas import Outcome


def resolve_outcome(session: Session, outcome: Outcome) -> OutcomeModel:
    """Write the outcome row and flip the signal status; PK enforces once-only."""
    signal = session.get(SignalModel, outcome.signal_id)
    if signal is None:
        raise LookupError(f"cannot resolve outcome for unknown signal: {outcome.signal_id}")
    signal.status = outcome.result
    signal.updated_at = outcome.resolved_at
    row = OutcomeModel(
        signal_id=outcome.signal_id,
        result=outcome.result,
        resolved_at=outcome.resolved_at,
        r_multiple=outcome.r_multiple,
        max_favorable=outcome.max_favorable,
        max_adverse=outcome.max_adverse,
    )
    session.add(row)
    session.commit()
    return session.get(OutcomeModel, outcome.signal_id)  # type: ignore[return-value]


def get_outcome(session: Session, signal_id: str) -> OutcomeModel | None:
    """Fetch the outcome row for a signal, if any."""
    return session.get(OutcomeModel, signal_id)


def list_outcomes(session: Session, limit: int = 100) -> list[OutcomeModel]:
    """Most recently resolved outcomes first."""
    stmt = select(OutcomeModel).order_by(OutcomeModel.resolved_at.desc()).limit(limit)
    return list(session.exec(stmt).scalars().all())  # type: ignore
