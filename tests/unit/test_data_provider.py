from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from jarvis.data import DataProvider, MockProvider
from jarvis.schemas import Candle, SymbolInfo, Tick

FIXTURES = Path(__file__).parents[1] / "fixtures"


def test_mock_provider_returns_newest_candles_in_ascending_order() -> None:
    provider: DataProvider = MockProvider(FIXTURES)

    candles = provider.get_candles("SYNTHETIC_XAUUSD", "M15", 2)

    assert [candle.timestamp.minute for candle in candles] == [15, 30]
    assert [candle.close for candle in candles] == [2002.0, 2003.0]


def test_mock_provider_rejects_nonpositive_limit() -> None:
    provider = MockProvider(FIXTURES)

    with pytest.raises(ValueError, match="n must be positive"):
        provider.get_candles("SYNTHETIC_XAUUSD", "M15", 0)


def test_mock_provider_does_not_invent_market_metadata() -> None:
    provider = MockProvider(FIXTURES)

    with pytest.raises(KeyError, match="No symbol info supplied"):
        provider.get_symbol_info("XAUUSD")
    with pytest.raises(KeyError, match="No tick supplied"):
        provider.get_tick("XAUUSD")


def test_mock_provider_returns_injected_metadata() -> None:
    info = SymbolInfo(
        symbol="XAUUSD",
        digits=2,
        point=0.01,
        trade_tick_size=0.01,
        trade_tick_value=1.0,
        volume_min=0.01,
        volume_max=10.0,
        volume_step=0.01,
    )
    tick = Tick(timestamp=datetime.now(UTC), bid=2000.0, ask=2000.1)
    provider = MockProvider(FIXTURES, {"XAUUSD": info}, {"XAUUSD": tick})

    assert provider.get_symbol_info("XAUUSD") is info
    assert provider.get_tick("XAUUSD") is tick


def test_candle_rejects_naive_timestamp_and_inconsistent_ohlc() -> None:
    with pytest.raises(ValidationError, match="timestamp must include a timezone"):
        Candle(
            timestamp=datetime(2026, 1, 1),
            open=10,
            high=11,
            low=9,
            close=10,
            volume=1,
        )
    with pytest.raises(ValidationError, match="high must be at least"):
        Candle(
            timestamp=datetime(2026, 1, 1, tzinfo=UTC),
            open=10,
            high=9,
            low=8,
            close=10,
            volume=1,
        )


def test_tick_rejects_crossed_prices() -> None:
    with pytest.raises(ValidationError, match="ask must be at least bid"):
        Tick(timestamp=datetime.now(UTC), bid=10, ask=9)
