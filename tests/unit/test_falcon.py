from datetime import UTC, datetime, timedelta

from jarvis.schemas import Candle, MarketStructure
from jarvis.strategies import Falcon, StrategyContext


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


def test_falcon_detects_bullish_breakout() -> None:
    candles = _upward_candles(25)
    last_open = candles[-1].open
    candles[-1] = _candle(24, last_open, last_open + 0.5, last_open - 0.1, last_open + 0.4)
    ctx = StrategyContext(
        symbol="XAUUSD",
        candles={"M15": candles},
        market_structure=MarketStructure(
            symbol="XAUUSD",
            timeframe_trends={"M15": "UP"},
            key_levels=[],
            atr={"M15": 1.0},
            volatility_regime="NORMAL",
            session="LONDON",
        ),
        now=datetime(2026, 1, 1, tzinfo=UTC),
    )

    result = Falcon({}).analyse(ctx)

    assert len(result) == 1
    assert result[0].strategy == "falcon"
    assert result[0].direction == "BUY"
    assert result[0].entry > result[0].sl
    assert result[0].tp > result[0].entry
    assert any("breakout" in evidence for evidence in result[0].evidence)


def test_falcon_detects_bearish_breakout() -> None:
    candles = _downward_candles(25)
    last_open = candles[-1].open
    candles[-1] = _candle(24, last_open, last_open + 0.1, last_open - 0.5, last_open - 0.4)
    ctx = StrategyContext(
        symbol="XAUUSD",
        candles={"M15": candles},
        market_structure=MarketStructure(
            symbol="XAUUSD",
            timeframe_trends={"M15": "DOWN"},
            key_levels=[],
            atr={"M15": 1.0},
            volatility_regime="NORMAL",
            session="LONDON",
        ),
        now=datetime(2026, 1, 1, tzinfo=UTC),
    )

    result = Falcon({}).analyse(ctx)

    assert len(result) == 1
    assert result[0].strategy == "falcon"
    assert result[0].direction == "SELL"
    assert result[0].entry < result[0].sl
    assert result[0].tp < result[0].entry
    assert any("breakout" in evidence for evidence in result[0].evidence)


def test_falcon_returns_empty_when_range() -> None:
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
            key_levels=[],
            atr={"M15": 1.0},
            volatility_regime="NORMAL",
            session="UNKNOWN",
        ),
        now=datetime(2026, 1, 1, tzinfo=UTC),
    )

    assert Falcon({}).analyse(ctx) == []


def test_falcon_returns_empty_without_breakout() -> None:
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

    assert Falcon({}).analyse(ctx) == []