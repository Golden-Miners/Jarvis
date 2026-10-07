"""Signal persistence (idempotent upserts, unique-OPEN enforcement)."""
# mypy: ignore-errors
from datetime import UTC, datetime

from sqlalchemy import select
from sqlmodel import Session

from jarvis.db.models import SignalModel
from jarvis.schemas import Signal


def _to_row(signal: Signal, cycle_id: str) -> SignalModel:
    """Map a schemas.Signal onto its table row."""
    return SignalModel(
        id=signal.id,
        cycle_id=cycle_id,
        symbol=signal.symbol,
        decision=signal.decision,
        direction=signal.direction,
        entry=signal.entry,
        sl=signal.sl,
        tp=signal.tp,
        rr=signal.rr,
        confidence=signal.confidence,
        score=signal.score,
        no_trade_reason="no_trade_reason_in_signal" if signal.decision == "NO_TRADE" else None,
        rationale=signal.rationale,
        status=signal.status,
        created_at=signal.created_at,
        expires_at=signal.expires_at,
        updated_at=datetime.now(UTC),
    )


def upsert_signal(session: Session, signal: Signal, cycle_id: str) -> SignalModel:
    """Insert or update a signal; raises IntegrityError on unique-OPEN violation."""
    row = _to_row(signal, cycle_id)
    merged = session.merge(row)
    session.commit()
    return merged


def get_signal(session: Session, signal_id: str) -> SignalModel | None:
    """Fetch one signal by id."""
    return session.get(SignalModel, signal_id)


def get_open_signals(session: Session, symbol: str | None = None) -> list[SignalModel]:
    """All OPEN signals, optionally for one symbol, oldest first."""
    stmt = select(SignalModel).where(SignalModel.status == "OPEN")
    if symbol is not None:
        stmt = stmt.where(SignalModel.symbol == symbol)
    stmt = stmt.order_by(SignalModel.created_at)  # type: ignore
    return list(session.exec(stmt).scalars().all())  # type: ignore


def list_signals(session: Session, limit: int = 100) -> list[SignalModel]:
    """Most recent signals first."""
    stmt = select(SignalModel).order_by(SignalModel.created_at.desc()).limit(limit)  # type: ignore
    return list(session.exec(stmt).scalars().all())  # type: ignore
