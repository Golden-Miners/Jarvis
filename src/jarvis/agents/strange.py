from collections.abc import Sequence
from datetime import UTC, datetime, time
from typing import Literal

from jarvis.config.models import DoctorStrangeSettings, InstrumentConfig, SessionWindow
from jarvis.indicators import atr, ema, structure_breaks, swings
from jarvis.schemas import Candle, MarketStructure, StructureBreak

Trend = Literal["UP", "DOWN", "RANGE"]
VolatilityRegime = Literal["LOW", "NORMAL", "HIGH"]


def run_strange(
    instrument: InstrumentConfig,
    candles_by_timeframe: dict[str, Sequence[Candle]],
    settings: DoctorStrangeSettings,
    session_windows: Sequence[SessionWindow],
    now: datetime,
) -> MarketStructure:
    """Summarize deterministic multi-timeframe market structure."""
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("now must be timezone-aware")
    if settings.primary_timeframe not in candles_by_timeframe:
        raise ValueError(f"missing primary timeframe {settings.primary_timeframe}")
    if not candles_by_timeframe:
        raise ValueError("candles_by_timeframe cannot be empty")

    trends: dict[str, Trend] = {}
    atr_values: dict[str, float] = {}
    for timeframe, candles in candles_by_timeframe.items():
        if not candles:
            raise ValueError(f"no candles for timeframe {timeframe}")
        _ensure_chronological(candles, timeframe)
        trends[timeframe] = _trend(candles, settings.ema_period)
        atr_series = atr(candles, settings.atr_period)
        latest_atr = atr_series[-1]
        if latest_atr is not None:
            atr_values[timeframe] = latest_atr

    primary = candles_by_timeframe[settings.primary_timeframe]
    if settings.primary_timeframe not in atr_values:
        raise ValueError("insufficient primary timeframe candles for ATR")
    pivots = swings(primary, settings.swing_left, settings.swing_right)
    breaks = structure_breaks(primary, pivots, trends[settings.primary_timeframe])
    levels = sorted({point.price for point in pivots})
    regime = _volatility_regime(atr(primary, settings.atr_period), settings)
    session = _session_name(now.astimezone(UTC).time(), session_windows)
    # Add primary trend key for Jarvis supervisor
    trends_with_primary = dict(trends)
    trends_with_primary["primary"] = trends[settings.primary_timeframe]
    return MarketStructure(
        symbol=instrument.symbol,
        timeframe_trends=trends_with_primary,
        last_bos=_latest_break(breaks, "BOS"),
        last_choch=_latest_break(breaks, "CHOCH"),
        key_levels=levels,
        atr=atr_values,
        volatility_regime=regime,
        session=session,
    )


def _ensure_chronological(candles: Sequence[Candle], timeframe: str) -> None:
    timestamps = [candle.timestamp for candle in candles]
    if timestamps != sorted(timestamps) or len(timestamps) != len(set(timestamps)):
        raise ValueError(f"candles for {timeframe} must be strictly chronological")


def _trend(candles: Sequence[Candle], period: int) -> Trend:
    values = ema([candle.close for candle in candles], period)
    if candles[-1].close > values[-1]:
        return "UP"
    if candles[-1].close < values[-1]:
        return "DOWN"
    return "RANGE"


def _volatility_regime(
    values: Sequence[float | None], settings: DoctorStrangeSettings
) -> VolatilityRegime:
    available = [value for value in values if value is not None]
    window = available[-settings.volatility_window :]
    if not window:
        raise ValueError("insufficient candles for volatility regime")
    current = window[-1]
    below = sum(value < current for value in window)
    tied = sum(value == current for value in window)
    rank = (below + tied / 2) / len(window)
    if rank <= settings.low_volatility_percentile:
        return "LOW"
    if rank >= settings.high_volatility_percentile:
        return "HIGH"
    return "NORMAL"


def _session_name(
    current: time, windows: Sequence[SessionWindow]
) -> str:
    for window in windows:
        start = window.start_utc
        end = window.end_utc
        if (start <= current < end) if start <= end else (current >= start or current < end):
            return window.name
    return "UNKNOWN"


def _latest_break(
    breaks: Sequence[StructureBreak], kind: Literal["BOS", "CHOCH"]
) -> dict[str, object] | None:
    for event in reversed(breaks):
        if event.kind == kind:
            return event.model_dump(mode="json")
    return None
