from datetime import UTC, datetime, timedelta

from jarvis.schemas import Candle, MarketStructure
from jarvis.strategies import BlackWidow, StrategyContext


def _candle(index: int, open_price: float, high: float, low: float, close: float) -> Candle:
    return Candle(
        timestamp=datetime(2026, 1, 1, tzinfo=UTC) + timedelta(minutes=index * 15),
        open=open_price,
        high=high,
        low=low,
        close=close,
        volume=1,
    )


def _upward_candles(count: int, start_open: float = 100.0, step: float = 0.2) -> list[Candle]:
    candles: list[Candle] = []
    for index in range(count):
        open_price = start_open + index * step
        high = open_price + 0.1
        low = open_price - 0.1
        close = open_price + step * 0.4
        candles.append(_candle(index, open_price, high, low, close))
    return candles


def _downward_candles(count: int, start_open: float = 110.0, step: float = 0.2) -> list[Candle]:
    candles: list[Candle] = []
    for index in range(count):
        open_price = start_open - index * step
        high = open_price + 0.1
        low = open_price - 0.1
        close = open_price - step * 0.4
        candles.append(_candle(index, open_price, high, low, close))
    return candles


def test_black_widow_detects_bullish_ema_pullback() -> None:
    candles: list[Candle] = []
    for index in range(20):
        open_price = 100.0 + index * 0.2
        high = open_price + 0.1
        low = open_price - 0.1
        close = open_price + 0.08
        candles.append(_candle(index, open_price, high, low, close))
    for index in range(20, 24):
        open_price = 104.0
        high = open_price + 0.15
        low = 99.2
        close = 99.5
        candles.append(_candle(index, open_price, high, low, close))
    last_open = 99.5
    candles.append(_candle(24, last_open, last_open + 0.1, last_open - 0.05, last_open + 0.06))

    ctx = StrategyContext(
        symbol="XAUUSD",
        candles={"M15": candles},
        market_structure=MarketStructure(
            symbol="XAUUSD",
            timeframe_trends={"M15": "UP"},
            key_levels=[99.0, 100.0],
            atr={"M15": 1.0},
            volatility_regime="NORMAL",
            session="LONDON",
        ),
        now=datetime(2026, 1, 1, tzinfo=UTC),
    )

    result = BlackWidow({}).analyse(ctx)

    assert len(result) == 1
    assert result[0].strategy == "black_widow"
    assert result[0].direction == "BUY"
    assert result[0].entry > result[0].sl
    assert result[0].tp > result[0].entry
    assert any("EMA" in evidence for evidence in result[0].evidence)


def test_black_widow_detects_bearish_ema_pullback() -> None:
    candles: list[Candle] = []
    for index in range(20):
        open_price = 110.0 - index * 0.2
        high = open_price + 0.1
        low = open_price - 0.1
        close = open_price - 0.08
        candles.append(_candle(index, open_price, high, low, close))
    for index in range(20, 24):
        open_price = 106.0
        high = 110.8
        low = open_price - 0.15
        close = 110.5
        candles.append(_candle(index, open_price, high, low, close))
    last_open = 110.5
    candles.append(_candle(24, last_open, last_open + 0.05, last_open - 0.1, last_open - 0.06))

    ctx = StrategyContext(
        symbol="XAUUSD",
        candles={"M15": candles},
        market_structure=MarketStructure(
            symbol="XAUUSD",
            timeframe_trends={"M15": "DOWN"},
            key_levels=[111.0, 110.0],
            atr={"M15": 1.0},
            volatility_regime="NORMAL",
            session="LONDON",
        ),
        now=datetime(2026, 1, 1, tzinfo=UTC),
    )

    result = BlackWidow({}).analyse(ctx)

    assert len(result) == 1
    assert result[0].strategy == "black_widow"
    assert result[0].direction == "SELL"
    assert result[0].entry < result[0].sl
    assert result[0].tp < result[0].entry
    assert any("EMA" in evidence for evidence in result[0].evidence)


def test_black_widow_returns_empty_when_range() -> None:
    candles = [
        _candle(
            i,
            100.0 + (i % 3) * 0.1,
            100.3 + (i % 3) * 0.1,
            99.7 + (i % 3) * 0.1,
            100.1 + (i % 3) * 0.1,
        )
        for i in range(25)
    ]
    ctx = StrategyContext(
        symbol="XAUUSD",
        candles={"M15": candles},
        market_structure=MarketStructure(
            symbol="XAUUSD",
            timeframe_trends={"M15": "RANGE"},
            key_levels=[100.0, 101.0],
            atr={"M15": 1.0},
            volatility_regime="NORMAL",
            session="UNKNOWN",
        ),
        now=datetime(2026, 1, 1, tzinfo=UTC),
    )

    assert BlackWidow({}).analyse(ctx) == []


def test_black_widow_returns_empty_without_ema_touch() -> None:
    candles = _upward_candles(25)
    ctx = StrategyContext(
        symbol="XAUUSD",
        candles={"M15": candles},
        market_structure=MarketStructure(
            symbol="XAUUSD",
            timeframe_trends={"M15": "UP"},
            key_levels=[],
            atr={"M15": 1.0},
            volatility_regime="NORMAL",
            session="UNKNOWN",
        ),
        now=datetime(2026, 1, 1, tzinfo=UTC),
    )

    assert BlackWidow({}).analyse(ctx) == []