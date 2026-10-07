"""Market structure and key levels persistence."""
# mypy: ignore-errors
from datetime import datetime

from sqlalchemy import select
from sqlmodel import Session

from jarvis.db.models import KeyLevelModel, MarketStructureModel


def upsert_market_structure(
    session: Session,
    *,
    id: str,
    cycle_id: str,
    symbol: str,
    trend_m15: str | None,
    trend_h1: str | None,
    trend_h4: str | None,
    trend_d1: str | None,
    atr_m15: float | None,
    atr_h1: float | None,
    volatility_regime: str | None,
    session_name: str,
    last_bos_direction: str | None,
    last_choch_direction: str | None,
    created_at: datetime,
) -> MarketStructureModel:
    """Insert or update a market structure snapshot."""
    row = MarketStructureModel(
        id=id,
        cycle_id=cycle_id,
        symbol=symbol,
        trend_m15=trend_m15,
        trend_h1=trend_h1,
        trend_h4=trend_h4,
        trend_d1=trend_d1,
        atr_m15=atr_m15,
        atr_h1=atr_h1,
        volatility_regime=volatility_regime,
        session=session_name,
        last_bos_direction=last_bos_direction,
        last_choch_direction=last_choch_direction,
        created_at=created_at,
    )
    merged = session.merge(row)
    session.commit()
    return merged


def get_market_structure(session: Session, id: str) -> MarketStructureModel | None:
    """Fetch a market structure by id."""
    return session.get(MarketStructureModel, id)


def list_market_structures(
    session: Session, cycle_id: str | None = None, symbol: str | None = None, limit: int = 100
) -> list[MarketStructureModel]:
    """List market structures, optionally filtered."""
    stmt = select(MarketStructureModel)
    if cycle_id:
        stmt = stmt.where(MarketStructureModel.cycle_id == cycle_id)
    if symbol:
        stmt = stmt.where(MarketStructureModel.symbol == symbol)
    stmt = stmt.order_by(MarketStructureModel.created_at.desc()).limit(limit)
    return list(session.exec(stmt).scalars().all())  # type: ignore


def upsert_key_level(
    session: Session,
    *,
    id: str,
    structure_id: str,
    price: float,
    kind: str,
) -> KeyLevelModel:
    """Insert or update a key level."""
    row = KeyLevelModel(id=id, structure_id=structure_id, price=price, kind=kind)
    merged = session.merge(row)
    session.commit()
    return merged


def get_key_levels(session: Session, structure_id: str) -> list[KeyLevelModel]:
    """Fetch all key levels for a structure."""
    stmt = select(KeyLevelModel).where(KeyLevelModel.structure_id == structure_id)
    return list(session.exec(stmt).scalars().all())  # type: ignore