from datetime import UTC, datetime, timedelta

from jarvis.schemas import Candle, MarketStructure
from jarvis.strategies import Hawkeye, StrategyContext


def _candle(index: int, open_price: float, high: float, low: float, close: float) -> Candle:
    return Candle(
        timestamp=datetime(2026, 1, 1, tzinfo=UTC) + timedelta(minutes=index * 15),
        open=open_price,
        high=high,
        low=low,
        close=close,
        volume=1,
    )


def test_hawkeye_detects_bullish_fvg_setup() -> None:
    candles = [
        _candle(0, 100.0, 101.0, 99.0, 100.0),
        _candle(1, 101.2, 102.0, 100.8, 101.3),
        _candle(2, 101.6, 102.2, 101.6, 101.8),
        *[
            _candle(
                index,
                101.7 + index * 0.04,
                102.2 + index * 0.04,
                101.1 + index * 0.03,
                101.9 + index * 0.05,
            )
            for index in range(3, 25)
        ],
    ]
    ctx = StrategyContext(
        symbol="XAUUSD",
        candles={"M15": candles},
        market_structure=MarketStructure(
            symbol="XAUUSD",
            timeframe_trends={"M15": "UP"},
            key_levels=[100.5, 101.2, 101.8],
            atr={"M15": 1.0},
            volatility_regime="NORMAL",
            session="LONDON",
        ),
        now=datetime(2026, 1, 1, tzinfo=UTC),
    )

    result = Hawkeye({}).analyse(ctx)

    assert len(result) == 1
    assert result[0].strategy == "hawkeye"
    assert result[0].direction == "BUY"
    assert result[0].entry > result[0].sl
    assert result[0].tp > result[0].entry
    assert any("bullish FVG" in evidence for evidence in result[0].evidence)


def test_hawkeye_returns_empty_when_no_structure_alignment() -> None:
    candles = [
        _candle(i, 100.0 + i * 0.1, 100.4 + i * 0.1, 99.7 + i * 0.1, 100.1 + i * 0.1)
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

    assert Hawkeye({}).analyse(ctx) == []
