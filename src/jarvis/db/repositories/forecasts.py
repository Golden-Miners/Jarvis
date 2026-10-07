"""Forecast persistence (TimesFM / Quicksilver)."""
# mypy: ignore-errors
from datetime import datetime

from sqlalchemy import select
from sqlmodel import Session

from jarvis.db.models import ForecastModel


def upsert_forecast(
    session: Session,
    *,
    id: str,
    cycle_id: str,
    symbol: str,
    timeframe: str,
    horizon_bars: int,
    expected_direction: str,
    strength: float,
    median_end: float,
    q10_end: float,
    q90_end: float,
    model_version: str,
    created_at: datetime,
) -> ForecastModel:
    """Insert or update a forecast."""
    row = ForecastModel(
        id=id,
        cycle_id=cycle_id,
        symbol=symbol,
        timeframe=timeframe,
        horizon_bars=horizon_bars,
        expected_direction=expected_direction,
        strength=strength,
        median_end=median_end,
        q10_end=q10_end,
        q90_end=q90_end,
        model_version=model_version,
        created_at=created_at,
    )
    merged = session.merge(row)
    session.commit()
    return merged


def get_forecast(session: Session, id: str) -> ForecastModel | None:
    """Fetch a forecast by id."""
    return session.get(ForecastModel, id)


def list_forecasts(
    session: Session,
    cycle_id: str | None = None,
    symbol: str | None = None,
    limit: int = 100,
) -> list[ForecastModel]:
    """List forecasts, optionally filtered."""
    stmt = select(ForecastModel)
    if cycle_id:
        stmt = stmt.where(ForecastModel.cycle_id == cycle_id)
    if symbol:
        stmt = stmt.where(ForecastModel.symbol == symbol)
    stmt = stmt.order_by(ForecastModel.created_at.desc()).limit(limit)
    return list(session.exec(stmt).scalars().all())  # type: ignore