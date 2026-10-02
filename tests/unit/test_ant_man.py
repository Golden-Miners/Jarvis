"""Tests for Ant-Man mean-reversion strategy (T3.5)."""

from datetime import UTC, datetime, timedelta

import pytest

from jarvis.schemas import Candle, MarketStructure
from jarvis.strategies import StrategyContext
from jarvis.strategies.ant_man import AntMan


def _candle(index: int, open_price: float, high: float, low: float, close: float) -> Candle:
    return Candle(
        timestamp=datetime(2026, 1, 1, tzinfo=UTC) + timedelta(minutes=index * 15),
        open=open_price,
        high=high,
        low=low,
        close=close,
        volume=1,
    )


def _ranging_candles(
    count: int,
    center: float = 100.0,
    amplitude: float = 0.2,
) -> list[Candle]:
    """Produce oscillating candles around `center` with given amplitude."""
    candles: list[Candle] = []
    for i in range(count):
        # Alternate between slight up/down to form a range
        direction = 1 if i % 2 == 0 else -1
        op = center + direction * amplitude * 0.3
        cl = center - direction * amplitude * 0.3
        hi = max(op, cl) + amplitude * 0.2
        lo = min(op, cl) - amplitude * 0.2
        candles.append(_candle(i, op, hi, lo, cl))
    return candles


def _range_market_structure(timeframe: str = "M15") -> MarketStructure:
    return MarketStructure(
        symbol="XAUUSD",
        timeframe_trends={timeframe: "RANGE"},
        key_levels=[99.0, 101.0],
        atr={timeframe: 0.5},
        volatility_regime="NORMAL",
        session="LONDON",
    )


def _trend_market_structure(direction: str = "UP", timeframe: str = "M15") -> MarketStructure:
    return MarketStructure(
        symbol="XAUUSD",
        timeframe_trends={timeframe: direction},
        key_levels=[],
        atr={timeframe: 0.5},
        volatility_regime="NORMAL",
        session="LONDON",
    )


# ---------------------------------------------------------------------------
# Bullish reversion: price slumped far below EMA, now recovering
# ---------------------------------------------------------------------------

def test_ant_man_detects_bullish_reversion() -> None:
    """Price extended far below EMA with a bullish recovery candle → BUY signal."""
    # 30 flat candles centred at 100 (EMA ~100)
    candles = _ranging_candles(30, center=100.0, amplitude=0.1)

    # Last two candles: price drops 3 ATR below EMA then prints bullish recovery
    # ATR default period=14; with amplitude ~0.1 ATR ≈ 0.1; extension_atr default=1.5
    # Need gap >= 1.5 * ATR ≈ 0.15. Drop by 0.3 to be safe.
    candles[-2] = _candle(28, 99.6, 99.65, 99.5, 99.55)   # dropped below EMA
    candles[-1] = _candle(29, 99.55, 99.75, 99.50, 99.70)  # bullish recovery (close > open & prev)

    ctx = StrategyContext(
        symbol="XAUUSD",
        candles={"M15": candles},
        market_structure=_range_market_structure(),
        now=datetime(2026, 1, 1, tzinfo=UTC),
    )

    result = AntMan({}).analyse(ctx)

    assert len(result) == 1
    setup = result[0]
    assert setup.strategy == "ant_man"
    assert setup.direction == "BUY"
    assert setup.entry > setup.sl
    assert setup.tp > setup.entry
    assert any("mean reversion" in e for e in setup.evidence)
    assert any("EMA" in e for e in setup.evidence)


# ---------------------------------------------------------------------------
# Bearish reversion: price surged far above EMA, now rejecting
# ---------------------------------------------------------------------------

def test_ant_man_detects_bearish_reversion() -> None:
    """Price extended far above EMA with a bearish rejection candle → SELL signal."""
    candles = _ranging_candles(30, center=100.0, amplitude=0.1)

    # Price surges above EMA then rejects
    candles[-2] = _candle(28, 100.4, 100.55, 100.35, 100.45)  # surged above EMA
    # bearish rejection candle: close < open and below previous close
    candles[-1] = _candle(29, 100.45, 100.50, 100.25, 100.30)

    ctx = StrategyContext(
        symbol="XAUUSD",
        candles={"M15": candles},
        market_structure=_range_market_structure(),
        now=datetime(2026, 1, 1, tzinfo=UTC),
    )

    result = AntMan({}).analyse(ctx)

    assert len(result) == 1
    setup = result[0]
    assert setup.strategy == "ant_man"
    assert setup.direction == "SELL"
    assert setup.entry < setup.sl
    assert setup.tp < setup.entry
    assert any("mean reversion" in e for e in setup.evidence)


# ---------------------------------------------------------------------------
# Disabled in trend (UP or DOWN) — must return empty
# ---------------------------------------------------------------------------

def test_ant_man_returns_empty_in_uptrend() -> None:
    """Ant-Man must not fire in an UP trend."""
    candles = _ranging_candles(30, center=100.0, amplitude=0.1)
    candles[-1] = _candle(29, 99.55, 99.75, 99.50, 99.70)

    ctx = StrategyContext(
        symbol="XAUUSD",
        candles={"M15": candles},
        market_structure=_trend_market_structure("UP"),
        now=datetime(2026, 1, 1, tzinfo=UTC),
    )

    assert AntMan({}).analyse(ctx) == []


def test_ant_man_returns_empty_in_downtrend() -> None:
    """Ant-Man must not fire in a DOWN trend."""
    candles = _ranging_candles(30, center=100.0, amplitude=0.1)
    candles[-1] = _candle(29, 100.45, 100.50, 100.25, 100.30)

    ctx = StrategyContext(
        symbol="XAUUSD",
        candles={"M15": candles},
        market_structure=_trend_market_structure("DOWN"),
        now=datetime(2026, 1, 1, tzinfo=UTC),
    )

    assert AntMan({}).analyse(ctx) == []


# ---------------------------------------------------------------------------
# No signal when price is close to EMA (not overextended)
# ---------------------------------------------------------------------------

def test_ant_man_returns_empty_when_not_overextended() -> None:
    """No signal when price is near EMA — extension threshold not reached."""
    candles = _ranging_candles(30, center=100.0, amplitude=0.1)
    # Price barely below EMA (well within extension_atr=1.5 × ATR)
    candles[-1] = _candle(29, 99.95, 100.00, 99.90, 99.97)

    ctx = StrategyContext(
        symbol="XAUUSD",
        candles={"M15": candles},
        market_structure=_range_market_structure(),
        now=datetime(2026, 1, 1, tzinfo=UTC),
    )

    assert AntMan({}).analyse(ctx) == []


# ---------------------------------------------------------------------------
# Too few candles — gracefully return empty
# ---------------------------------------------------------------------------

def test_ant_man_returns_empty_with_insufficient_candles() -> None:
    """Fewer than 20 candles → no analysis possible."""
    candles = _ranging_candles(10)
    ctx = StrategyContext(
        symbol="XAUUSD",
        candles={"M15": candles},
        market_structure=_range_market_structure(),
        now=datetime(2026, 1, 1, tzinfo=UTC),
    )

    assert AntMan({}).analyse(ctx) == []


# ---------------------------------------------------------------------------
# SL/TP direction sanity
# ---------------------------------------------------------------------------

def test_ant_man_bullish_setup_price_relationships() -> None:
    """BUY setup: SL < entry < TP invariant must hold."""
    candles = _ranging_candles(30, center=100.0, amplitude=0.1)
    candles[-2] = _candle(28, 99.6, 99.65, 99.5, 99.55)
    candles[-1] = _candle(29, 99.55, 99.75, 99.50, 99.70)

    ctx = StrategyContext(
        symbol="XAUUSD",
        candles={"M15": candles},
        market_structure=_range_market_structure(),
        now=datetime(2026, 1, 1, tzinfo=UTC),
    )
    result = AntMan({}).analyse(ctx)
    if result:
        s = result[0]
        assert s.sl < s.entry < s.tp, f"BUY invariant violated: SL={s.sl} entry={s.entry} TP={s.tp}"


# ---------------------------------------------------------------------------
# Param validation
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "bad_params",
    [
        {"ema_period": 0},
        {"atr_period": -1},
        {"extension_atr": 0},
        {"rr_multiple": 0},
        {"min_confidence": 1.5},
        {"min_confidence": -0.1},
    ],
)
def test_ant_man_rejects_invalid_params(bad_params: dict[str, object]) -> None:
    """Invalid strategy params must raise ValueError before any analysis."""
    candles = _ranging_candles(30, center=100.0, amplitude=0.1)
    candles[-2] = _candle(28, 99.6, 99.65, 99.5, 99.55)
    candles[-1] = _candle(29, 99.55, 99.75, 99.50, 99.70)

    ctx = StrategyContext(
        symbol="XAUUSD",
        candles={"M15": candles},
        market_structure=_range_market_structure(),
        now=datetime(2026, 1, 1, tzinfo=UTC),
    )
    with pytest.raises(ValueError):
        AntMan(bad_params).analyse(ctx)
