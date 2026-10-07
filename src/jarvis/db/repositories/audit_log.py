"""Audit log persistence (append-only)."""
# mypy: ignore-errors
from datetime import datetime

from sqlalchemy import select
from sqlmodel import Session

from jarvis.db.models import AuditLogModel


def append_audit_log(
    session: Session,
    *,
    id: str,
    ts: datetime,
    actor: str,
    action: str,
    entity: str | None,
    entity_id: str | None,
    payload: str | None,
) -> AuditLogModel:
    """Append an audit log entry (never modified)."""
    row = AuditLogModel(
        id=id,
        ts=ts,
        actor=actor,
        action=action,
        entity=entity,
        entity_id=entity_id,
        payload=payload,
    )
    session.add(row)
    session.commit()
    return row


def list_audit_log(
    session: Session,
    actor: str | None = None,
    entity: str | None = None,
    limit: int = 100,
) -> list[AuditLogModel]:
    """List audit log entries, optionally filtered."""
    stmt = select(AuditLogModel)
    if actor:
        stmt = stmt.where(AuditLogModel.actor == actor)
    if entity:
        stmt = stmt.where(AuditLogModel.entity == entity)
    stmt = stmt.order_by(AuditLogModel.ts.desc()).limit(limit)
    return list(session.exec(stmt).scalars().all())  # type: ignore