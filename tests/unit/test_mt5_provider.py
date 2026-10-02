from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from jarvis.data import MT5Provider


def _rate(timestamp: int, close: float = 10.0) -> dict[str, float | int]:
    return {
        "time": timestamp,
        "open": close,
        "high": close + 1,
        "low": close - 1,
        "close": close,
        "tick_volume": 12,
    }


class FakeMT5:
    TIMEFRAME_M15 = 15
    TIMEFRAME_H1 = 16385
    TIMEFRAME_M5 = 5
    TIMEFRAME_H4 = 16388
    TIMEFRAME_D1 = 16408

    def __init__(self, rates: list[dict[str, float | int]] | None = None) -> None:
        self.rates = rates or [_rate(1_767_225_600), _rate(1_767_224_700)]
        self.calls: list[tuple[Any, ...]] = []
        self.info = SimpleNamespace(
            digits=2,
            point=0.01,
            trade_tick_size=0.01,
            trade_tick_value=1.0,
            volume_min=0.01,
            volume_max=10.0,
            volume_step=0.01,
        )
        self.tick = SimpleNamespace(time=1_767_225_600, bid=10.0, ask=10.1)

    def initialize(self, **kwargs: Any) -> bool:
        self.calls.append(("initialize", kwargs))
        return True

    def shutdown(self) -> None:
        self.calls.append(("shutdown",))

    def copy_rates_from_pos(
        self, symbol: str, timeframe: int, start_pos: int, count: int
    ) -> list[dict[str, float | int]]:
        self.calls.append(("copy_rates_from_pos", symbol, timeframe, start_pos, count))
        return self.rates

    def symbol_info(self, symbol: str) -> SimpleNamespace:
        self.calls.append(("symbol_info", symbol))
        return self.info

    def symbol_info_tick(self, symbol: str) -> SimpleNamespace:
        self.calls.append(("symbol_info_tick", symbol))
        return self.tick


def test_provider_initializes_fetches_closed_bars_and_shuts_down(tmp_path: Path) -> None:
    api = FakeMT5()
    provider = MT5Provider(tmp_path, mt5_module=api)

    provider.initialize()
    candles = provider.get_candles("XAUUSD", "M15", 2, "GOLD")
    provider.shutdown()

    assert [candle.timestamp for candle in candles] == sorted(
        candle.timestamp for candle in candles
    )
    assert api.calls == [
        ("initialize", {}),
        ("copy_rates_from_pos", "GOLD", api.TIMEFRAME_M15, 1, 2),
        ("shutdown",),
    ]
    assert (tmp_path / "XAUUSD_M15.parquet").exists()


def test_provider_maps_symbol_info_and_tick(tmp_path: Path) -> None:
    api = FakeMT5()
    provider = MT5Provider(tmp_path, mt5_module=api)

    info = provider.get_symbol_info("XAUUSD", "GOLD")
    tick = provider.get_tick("XAUUSD", "GOLD")

    assert info.symbol == "XAUUSD"
    assert info.digits == 2
    assert tick.bid == 10.0
    assert tick.ask == 10.1
    assert api.calls == [("symbol_info", "GOLD"), ("symbol_info_tick", "GOLD")]


def test_provider_rejects_unsupported_timeframe_before_api_call(tmp_path: Path) -> None:
    api = FakeMT5()
    provider = MT5Provider(tmp_path, mt5_module=api)

    with pytest.raises(ValueError, match="Unsupported timeframe"):
        provider.get_candles("XAUUSD", "M1", 2)
    assert api.calls == []


def test_provider_rejects_duplicate_timestamps(tmp_path: Path) -> None:
    timestamp = 1_767_225_600
    api = FakeMT5([_rate(timestamp), _rate(timestamp)])
    provider = MT5Provider(tmp_path, mt5_module=api)

    with pytest.raises(ValueError, match="duplicate candle timestamps"):
        provider.get_candles("XAUUSD", "M15", 2)


def test_provider_rejects_invalid_ohlc_data(tmp_path: Path) -> None:
    invalid = _rate(1_767_225_600)
    invalid["high"] = 8
    api = FakeMT5([invalid])
    provider = MT5Provider(tmp_path, mt5_module=api)

    with pytest.raises(ValueError, match="high must be at least"):
        provider.get_candles("XAUUSD", "M15", 1)


def test_provider_rejects_nonpositive_limit(tmp_path: Path) -> None:
    api = FakeMT5()
    provider = MT5Provider(tmp_path, mt5_module=api)

    with pytest.raises(ValueError, match="n must be positive"):
        provider.get_candles("XAUUSD", "M15", 0)
    assert api.calls == []


def test_cache_is_not_rewritten_without_a_new_bar(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import pandas as pd

    api = FakeMT5()
    provider = MT5Provider(tmp_path, mt5_module=api)
    provider.get_candles("XAUUSD", "M15", 2)
    cache_path = tmp_path / "XAUUSD_M15.parquet"
    original_mtime = cache_path.stat().st_mtime_ns
    original_to_parquet = pd.DataFrame.to_parquet
    writes = 0

    def track_write(self: pd.DataFrame, *args: Any, **kwargs: Any) -> None:
        nonlocal writes
        writes += 1
        original_to_parquet(self, *args, **kwargs)

    monkeypatch.setattr(pd.DataFrame, "to_parquet", track_write)
    provider.get_candles("XAUUSD", "M15", 2)

    assert writes == 0
    assert cache_path.stat().st_mtime_ns == original_mtime


def test_provider_uses_only_allowed_read_api_calls(tmp_path: Path) -> None:
    api = FakeMT5()
    provider = MT5Provider(tmp_path, terminal_path="terminal.exe", mt5_module=api)

    provider.initialize()
    provider.get_candles("XAUUSD", "M15", 2)
    provider.get_symbol_info("XAUUSD")
    provider.get_tick("XAUUSD")
    provider.shutdown()

    allowed = {
        "initialize",
        "copy_rates_from_pos",
        "symbol_info",
        "symbol_info_tick",
        "shutdown",
    }
    assert {call[0] for call in api.calls} <= allowed
    assert api.calls[0] == ("initialize", {"path": "terminal.exe"})


def test_mt5_epoch_timestamps_are_utc(tmp_path: Path) -> None:
    api = FakeMT5([_rate(1_767_225_600)])
    provider = MT5Provider(tmp_path, mt5_module=api)

    candle = provider.get_candles("XAUUSD", "M15", 1)[0]

    assert candle.timestamp.tzinfo == UTC
    assert candle.timestamp == datetime.fromtimestamp(1_767_225_600, UTC)
