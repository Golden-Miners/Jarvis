"""Cycle bookkeeping (idempotent upserts per Backend_Schema §5.5)."""
# mypy: ignore-errors
from datetime import UTC, datetime

from sqlalchemy import select
from sqlmodel import Session

from jarvis.db.models import ConfigSnapshotModel, CycleModel


def upsert_cycle(
    session: Session,
    cycle_id: str,
    trigger: str,
    config_hash: str,
    config_text: str,
    started_at: datetime | None = None,
) -> None:
    """Start or resume a cycle; re-running the same id never duplicates."""
    ts = started_at or datetime.now(UTC)
    snapshot = session.get(ConfigSnapshotModel, config_hash)
    if snapshot is None:
        session.add(ConfigSnapshotModel(hash=config_hash, yaml_text=config_text, created_at=ts))
    cycle = session.get(CycleModel, cycle_id)
    if cycle is None:
        session.add(
            CycleModel(
                id=cycle_id,
                trigger=trigger,
                status="RUNNING",
                config_hash=config_hash,
                started_at=ts,
            )
        )
    else:
        cycle.trigger = trigger
        cycle.status = "RUNNING"
        cycle.config_hash = config_hash
        cycle.started_at = ts
        cycle.finished_at = None
        cycle.duration_ms = None
    session.commit()


def complete_cycle(
    session: Session,
    cycle_id: str,
    status: str,
    finished_at: datetime | None = None,
    duration_ms: int | None = None,
) -> None:
    """Mark a cycle finished with its final status and duration."""
    ts = finished_at or datetime.now(UTC)
    cycle = session.get(CycleModel, cycle_id)
    if cycle is None:
        raise LookupError(f"unknown cycle: {cycle_id}")
    cycle.status = status
    cycle.finished_at = ts
    cycle.duration_ms = duration_ms
    session.commit()


def get_cycle(session: Session, cycle_id: str) -> CycleModel | None:
    """Fetch one cycle row by id."""
    return session.get(CycleModel, cycle_id)


def list_cycles(session: Session, limit: int = 100) -> list[CycleModel]:
    """Most recent cycles first."""
    stmt = select(CycleModel).order_by(CycleModel.started_at.desc()).limit(limit)
    return list(session.exec(stmt).scalars().all())  # type: ignore
