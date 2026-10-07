"""Setup candidate and risk assessment persistence."""
# mypy: ignore-errors
import json
from datetime import datetime

from sqlalchemy import select
from sqlmodel import Session

from jarvis.db.models import RiskAssessmentModel, SetupCandidateModel


def upsert_setup_candidate(
    session: Session,
    *,
    id: str,
    cycle_id: str,
    symbol: str,
    strategy: str,
    agent: str,
    direction: str,
    entry: float,
    sl: float,
    tp: float,
    confidence: float,
    evidence: list[str],
    created_at: datetime,
) -> SetupCandidateModel:
    """Insert or update a setup candidate."""
    row = SetupCandidateModel(
        id=id,
        cycle_id=cycle_id,
        symbol=symbol,
        strategy=strategy,
        agent=agent,
        direction=direction,
        entry=entry,
        sl=sl,
        tp=tp,
        confidence=confidence,
        evidence=json.dumps(evidence),
        created_at=created_at,
    )
    merged = session.merge(row)
    session.commit()
    return merged


def get_setup_candidate(session: Session, id: str) -> SetupCandidateModel | None:
    """Fetch a setup candidate by id."""
    return session.get(SetupCandidateModel, id)


def list_setup_candidates(
    session: Session,
    cycle_id: str | None = None,
    symbol: str | None = None,
    limit: int = 100,
) -> list[SetupCandidateModel]:
    """List setup candidates, optionally filtered."""
    stmt = select(SetupCandidateModel)
    if cycle_id:
        stmt = stmt.where(SetupCandidateModel.cycle_id == cycle_id)
    if symbol:
        stmt = stmt.where(SetupCandidateModel.symbol == symbol)
    stmt = stmt.order_by(SetupCandidateModel.created_at.desc()).limit(limit)
    return list(session.exec(stmt).scalars().all())  # type: ignore


def upsert_risk_assessment(
    session: Session,
    *,
    id: str,
    candidate_id: str,
    valid: int,
    rr: float,
    sl_atr_mult: float,
    spread_ok: int,
    suggested_lot: float | None,
    issues: list[str],
    created_at: datetime,
) -> RiskAssessmentModel:
    """Insert or update a risk assessment."""
    row = RiskAssessmentModel(
        id=id,
        candidate_id=candidate_id,
        valid=valid,
        rr=rr,
        sl_atr_mult=sl_atr_mult,
        spread_ok=spread_ok,
        suggested_lot=suggested_lot,
        issues=json.dumps(issues),
        created_at=created_at,
    )
    merged = session.merge(row)
    session.commit()
    return merged


def get_risk_assessment(session: Session, candidate_id: str) -> RiskAssessmentModel | None:
    """Fetch risk assessment for a candidate."""
    stmt = select(RiskAssessmentModel).where(RiskAssessmentModel.candidate_id == candidate_id)
    return session.exec(stmt).scalars().first()  # type: ignore


def list_risk_assessments(session: Session, limit: int = 100) -> list[RiskAssessmentModel]:
    """List risk assessments."""
    stmt = select(RiskAssessmentModel).order_by(RiskAssessmentModel.created_at.desc()).limit(limit)
    return list(session.exec(stmt).scalars().all())  # type: ignore