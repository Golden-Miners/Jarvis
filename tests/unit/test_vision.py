from datetime import UTC, datetime
from typing import Any

import pytest

from jarvis.agents import run_vision
from jarvis.config.models import InstrumentConfig
from jarvis.schemas import Candle, SymbolInfo, Tick, VisionResult


class RecordingProvider:
    def __init__(self, failure: Exception | None = None) -> None:
        self.calls: list[tuple[Any, ...]] = []
        self.failure = failure

    def get_candles(
        self, symbol: str, tf: str, n: int, broker_symbol: str | None = None
    ) -> list[Candle]:
        self.calls.append(("candles", symbol, tf, n, broker_symbol))
        if self.failure:
            raise self.failure
        return [
            Candle(
                timestamp=datetime(2026, 1, 1, tzinfo=UTC),
                open=10,
                high=11,
                low=9,
                close=10.5,
                volume=3,
            )
        ]

    def get_symbol_info(
        self, symbol: str, broker_symbol: str | None = None
    ) -> SymbolInfo:
        self.calls.append(("symbol_info", symbol, broker_symbol))
        return SymbolInfo(
            symbol=symbol,
            digits=2,
            point=0.01,
            trade_tick_size=0.01,
            trade_tick_value=1,
            volume_min=0.01,
            volume_max=10,
            volume_step=0.01,
        )

    def get_tick(self, symbol: str, broker_symbol: str | None = None) -> Tick:
        self.calls.append(("tick", symbol, broker_symbol))
        return Tick(timestamp=datetime(2026, 1, 1, tzinfo=UTC), bid=10, ask=10.1)


def _instrument(symbol: str = "XAUUSD", broker_symbol: str = "GOLD") -> InstrumentConfig:
    return InstrumentConfig(
        symbol=symbol,
        broker_symbol=broker_symbol,
        agent="iron_man",
        sessions=[],
        atr_multipliers={},
    )


def test_vision_fetches_typed_market_data_for_all_timeframes() -> None:
    provider = RecordingProvider()
    timeframes = ["M5", "M15", "H1", "H4", "D1"]

    result = run_vision(provider, [_instrument()], timeframes, 128)

    assert isinstance(result, VisionResult)
    market_data = result.instruments["XAUUSD"]
    assert market_data.symbol_info.symbol == "XAUUSD"
    assert market_data.tick.ask == 10.1
    assert list(market_data.candles) == timeframes
    assert all(len(candles) == 1 for candles in market_data.candles.values())
    assert provider.calls[:5] == [
        ("candles", "XAUUSD", timeframe, 128, "GOLD") for timeframe in timeframes
    ]
    assert provider.calls[-2:] == [
        ("symbol_info", "XAUUSD", "GOLD"),
        ("tick", "XAUUSD", "GOLD"),
    ]


def test_vision_rejects_invalid_count_before_provider_access() -> None:
    provider = RecordingProvider()

    with pytest.raises(ValueError, match="candle_count must be positive"):
        run_vision(provider, [_instrument()], ["M15"], 0)

    assert provider.calls == []


def test_vision_rejects_empty_timeframes_before_provider_access() -> None:
    provider = RecordingProvider()

    with pytest.raises(ValueError, match="at least one timeframe"):
        run_vision(provider, [_instrument()], [], 10)

    assert provider.calls == []


def test_vision_propagates_provider_failure() -> None:
    failure = ConnectionError("provider unavailable")
    provider = RecordingProvider(failure)

    with pytest.raises(ConnectionError, match="provider unavailable"):
        run_vision(provider, [_instrument()], ["M15"], 10)
