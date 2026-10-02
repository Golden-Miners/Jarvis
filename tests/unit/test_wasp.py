"""Tests for Wasp supply-demand + Fib confluence strategy (T3.6)."""

from datetime import UTC, datetime, timedelta

import pytest

from jarvis.schemas import Candle, MarketStructure
from jarvis.strategies import StrategyContext
from jarvis.strategies.wasp import Wasp


def _candle(index: int, open_price: float, high: float, low: float, close: float) -> Candle:
    return Candle(
        timestamp=datetime(2026, 1, 1, tzinfo=UTC) + timedelta(minutes=index * 15),
        open=open_price,
        high=high,
        low=low,
        close=close,
        volume=1,
    )


def _trend_market_structure(direction: str = "UP", timeframe: str = "M15") -> MarketStructure:
    return MarketStructure(
        symbol="XAUUSD",
        timeframe_trends={timeframe: direction},
        key_levels=[],
        atr={timeframe: 1.0},
        volatility_regime="NORMAL",
        session="LONDON",
    )


def _triangle_wave(
    start_idx: int, count: int, period: int, center: float, amplitude: float
) -> list[Candle]:
    candles = []
    for i in range(count):
        phase = i % period
        val = phase / (period / 2) if phase < period / 2 else (period - phase) / (period / 2)
        price = center - amplitude + 2 * amplitude * val
        candles.append(_candle(start_idx + i, price, price+0.1, price-0.1, price))
    return candles

# ---------------------------------------------------------------------------
# Bullish Setup
# ---------------------------------------------------------------------------

def test_wasp_detects_bullish_setup() -> None:
    """Wasp detects a bullish retest of a Fib+Zone confluence."""
    # We want a zone at ~100. We create triangle waves centered at 100.
    # period=20 means peaks at +10 and -10 from center.
    candles = _triangle_wave(0, 60, 20, center=100.5, amplitude=0.5)
    # Troughs are at 100.0, peaks at 101.0. This creates a zone at 100.0 (troughs).

    # Now make a huge swing down to 90 and up to 110 to create Fib anchors.
    # From idx 60 (price 100), go down to 90.
    for i in range(10):
        price = 100 - i # 100 down to 91
        candles.append(_candle(60+i, price, price+0.1, price-0.1, price))
    candles.append(_candle(70, 90, 90.1, 89.9, 90)) # strict low at 90
    
    # Go up to 110
    for i in range(1, 20):
        price = 90 + i # 91 up to 109
        candles.append(_candle(70+i, price, price+0.1, price-0.1, price))
    candles.append(_candle(90, 110, 110.1, 109.9, 110)) # strict high at 110

    # Fib 0.5 is at 100. We already have a price zone at 100.
    # Pull back down to 100 to test the confluence.
    for i in range(1, 10):
        price = 110 - i # 109 down to 101
        candles.append(_candle(90+i, price, price+0.1, price-0.1, price))
    
    # Setup candles: drop to 100, then bullish bounce
    candles.append(_candle(100, 101, 101.5, 99.8, 100)) # drop to 100
    candles.append(_candle(101, 100, 102, 99.5, 101.5)) # bullish bounce

    ctx = StrategyContext(
        symbol="XAUUSD",
        candles={"M15": candles},
        market_structure=_trend_market_structure("UP"),
        now=datetime(2026, 1, 1, tzinfo=UTC),
    )

    result = Wasp({}).analyse(ctx)
    assert len(result) == 1
    setup = result[0]
    assert setup.strategy == "wasp"
    assert setup.direction == "BUY"
    assert setup.entry > setup.sl
    assert setup.tp > setup.entry
    assert any("bullish zone retest" in e for e in setup.evidence)
    assert any("confluence with Fib" in e for e in setup.evidence)


# ---------------------------------------------------------------------------
# Bearish Setup
# ---------------------------------------------------------------------------

def test_wasp_detects_bearish_setup() -> None:
    """Wasp detects a bearish retest of a Fib+Zone confluence."""
    # Zone at ~100.
    candles = _triangle_wave(0, 60, 20, center=99.5, amplitude=0.5)
    # Peaks at 100.0, troughs at 99.0. Zone at 100.0 (peaks).

    # From idx 60 (price 100), go up to 110.
    for i in range(10):
        price = 100 + i 
        candles.append(_candle(60+i, price, price+0.1, price-0.1, price))
    candles.append(_candle(70, 110, 110.1, 109.9, 110)) # strict high at 110
    
    # Go down to 90
    for i in range(1, 20):
        price = 110 - i 
        candles.append(_candle(70+i, price, price+0.1, price-0.1, price))
    candles.append(_candle(90, 90, 90.1, 89.9, 90)) # strict low at 90

    # Fib 0.5 is at 100. Pull back up to 100 to test the confluence.
    for i in range(1, 10):
        price = 90 + i 
        candles.append(_candle(90+i, price, price+0.1, price-0.1, price))
    
    # Setup candles: rise to 100, then bearish rejection
    candles.append(_candle(100, 99, 100.2, 98.8, 100)) # rise to 100
    candles.append(_candle(101, 100, 100.5, 98.5, 99)) # bearish reject

    ctx = StrategyContext(
        symbol="XAUUSD",
        candles={"M15": candles},
        market_structure=_trend_market_structure("DOWN"),
        now=datetime(2026, 1, 1, tzinfo=UTC),
    )

    result = Wasp({}).analyse(ctx)
    assert len(result) == 1
    setup = result[0]
    assert setup.strategy == "wasp"
    assert setup.direction == "SELL"
    assert setup.entry < setup.sl
    assert setup.tp < setup.entry
    assert any("bearish zone retest" in e for e in setup.evidence)
    assert any("confluence with Fib" in e for e in setup.evidence)


# ---------------------------------------------------------------------------
# Range Guard
# ---------------------------------------------------------------------------

def test_wasp_returns_empty_in_range_trend() -> None:
    """Wasp must not fire in a RANGE trend."""
    ctx = StrategyContext(
        symbol="XAUUSD",
        candles={"M15": [_candle(i, 100, 101, 99, 100) for i in range(100)]},
        market_structure=_trend_market_structure("RANGE"),
        now=datetime(2026, 1, 1, tzinfo=UTC),
    )
    assert Wasp({}).analyse(ctx) == []


# ---------------------------------------------------------------------------
# Insufficient Candles
# ---------------------------------------------------------------------------

def test_wasp_returns_empty_with_insufficient_candles() -> None:
    """Fewer than 50 candles → no analysis possible."""
    ctx = StrategyContext(
        symbol="XAUUSD",
        candles={"M15": [_candle(i, 100, 101, 99, 100) for i in range(40)]},
        market_structure=_trend_market_structure("UP"),
        now=datetime(2026, 1, 1, tzinfo=UTC),
    )
    assert Wasp({}).analyse(ctx) == []


# ---------------------------------------------------------------------------
# Param validation
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "bad_params",
    [
        {"swings_left": 0},
        {"zone_atr_tolerance": -1},
        {"rr_multiple": 0},
        {"min_confidence": 1.5},
        {"fib_ratios": "0.5"}, # not a list
    ],
)
def test_wasp_rejects_invalid_params(bad_params: dict[str, object]) -> None:
    """Invalid strategy params must raise ValueError before any analysis."""
    ctx = StrategyContext(
        symbol="XAUUSD",
        candles={"M15": [_candle(i, 100, 101, 99, 100) for i in range(100)]},
        market_structure=_trend_market_structure("UP"),
        now=datetime(2026, 1, 1, tzinfo=UTC),
    )
    with pytest.raises(ValueError):
        Wasp(bad_params).analyse(ctx)
