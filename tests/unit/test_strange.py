from datetime import UTC, datetime, time, timedelta

import pytest
from pydantic import ValidationError

from jarvis.agents import run_strange
from jarvis.config.models import DoctorStrangeSettings, InstrumentConfig, SessionWindow
from jarvis.schemas import Candle


def _settings(**overrides: object) -> DoctorStrangeSettings:
    values: dict[str, object] = {
        "primary_timeframe": "M15",
        "ema_period": 2,
        "atr_period": 2,
        "volatility_window": 3,
        "low_volatility_percentile": 0.2,
        "high_volatility_percentile": 0.8,
        "swing_left": 1,
        "swing_right": 1,
        "zone_tolerance": 0.5,
    }
    values.update(overrides)
    return DoctorStrangeSettings(**values)


def _instrument() -> InstrumentConfig:
    return InstrumentConfig(
        symbol="XAUUSD",
        broker_symbol="GOLD",
        agent="iron_man",
        sessions=[],
        atr_multipliers={},
    )


def _series(ranges: list[float], closes: list[float] | None = None) -> list[Candle]:
    close_values = closes or [100 + index for index in range(len(ranges))]
    candles = []
    for index, (range_size, close) in enumerate(zip(ranges, close_values, strict=True)):
        candles.append(
            Candle(
                timestamp=datetime(2026, 1, 1, tzinfo=UTC) + timedelta(minutes=15 * index),
                open=close - 0.2,
                high=close + range_size / 2,
                low=close - range_size / 2,
                close=close,
                volume=10,
            )
        )
    return candles


def test_run_strange_returns_mtf_trends_atr_levels_and_unknown_session() -> None:
    primary = _series([2, 2, 2, 2, 2], [100, 101, 102, 103, 104])
    higher = _series([4, 4, 4], [100, 99, 98])

    result = run_strange(
        _instrument(),
        {"M15": primary, "H1": higher},
        _settings(),
        [],
        datetime(2026, 1, 1, 12, tzinfo=UTC),
    )

    assert result.symbol == "XAUUSD"
    assert result.timeframe_trends == {"M15": "UP", "H1": "DOWN", "primary": "UP"}
    assert result.atr == {"M15": 2.0, "H1": 4.0}
    assert result.volatility_regime == "NORMAL"
    assert result.session == "UNKNOWN"
    assert result.last_bos is None
    assert result.last_choch is None


def test_run_strange_detects_explicit_session_and_overnight_window() -> None:
    candles = _series([2, 2, 2], [100, 101, 102])
    windows = [
        SessionWindow(name="OVERNIGHT", start_utc=time(22), end_utc=time(2)),
        SessionWindow(name="EUROPE", start_utc=time(7), end_utc=time(16)),
    ]

    result = run_strange(
        _instrument(),
        {"M15": candles},
        _settings(),
        windows,
        datetime(2026, 1, 1, 23, tzinfo=UTC),
    )

    assert result.session == "OVERNIGHT"


def test_run_strange_classifies_atr_rank_extremes() -> None:
    low = _series([3, 2, 1], [100, 101, 102])
    high = _series([1, 2, 3], [100, 101, 102])

    low_result = run_strange(
        _instrument(),
        {"M15": low},
        _settings(low_volatility_percentile=0.5, high_volatility_percentile=1.0),
        [],
        datetime(2026, 1, 1, tzinfo=UTC),
    )
    high_result = run_strange(
        _instrument(),
        {"M15": high},
        _settings(low_volatility_percentile=0.0, high_volatility_percentile=0.5),
        [],
        datetime(2026, 1, 1, tzinfo=UTC),
    )

    assert low_result.volatility_regime == "LOW"
    assert high_result.volatility_regime == "HIGH"


def test_run_strange_includes_latest_confirmed_structure_break() -> None:
    candles = [
        Candle(
            timestamp=datetime(2026, 1, 1, tzinfo=UTC),
            open=9,
            high=10,
            low=8,
            close=9,
            volume=1,
        ),
        Candle(
            timestamp=datetime(2026, 1, 1, 0, 15, tzinfo=UTC),
            open=10,
            high=12,
            low=9,
            close=11,
            volume=1,
        ),
        Candle(
            timestamp=datetime(2026, 1, 1, 0, 30, tzinfo=UTC),
            open=9,
            high=10,
            low=7,
            close=8,
            volume=1,
        ),
        Candle(
            timestamp=datetime(2026, 1, 1, 0, 45, tzinfo=UTC),
            open=9,
            high=11,
            low=8,
            close=10,
            volume=1,
        ),
        Candle(
            timestamp=datetime(2026, 1, 1, 1, 0, tzinfo=UTC),
            open=11,
            high=14,
            low=10,
            close=13,
            volume=1,
        ),
    ]

    result = run_strange(
        _instrument(),
        {"M15": candles},
        _settings(),
        [],
        datetime(2026, 1, 1, 1, tzinfo=UTC),
    )

    assert result.last_bos is not None
    assert result.last_bos["level"] == 12
    assert result.last_bos["direction"] == "UP"


def test_run_strange_requires_primary_timeframe_and_chronological_candles() -> None:
    candles = _series([2, 2, 2])

    with pytest.raises(ValueError, match="missing primary timeframe"):
        run_strange(
            _instrument(),
            {"H1": candles},
            _settings(),
            [],
            datetime(2026, 1, 1, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="strictly chronological"):
        run_strange(
            _instrument(),
            {"M15": list(reversed(candles))},
            _settings(),
            [],
            datetime(2026, 1, 1, tzinfo=UTC),
        )


def test_run_strange_requires_timezone_aware_analysis_time() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        run_strange(
            _instrument(),
            {"M15": _series([2, 2, 2])},
            _settings(),
            [],
            datetime(2026, 1, 1),
        )


def test_doctor_strange_settings_validate_rank_cutoffs() -> None:
    with pytest.raises(ValidationError):
        _settings(low_volatility_percentile=1.1)
    with pytest.raises(ValidationError, match="below high percentile"):
        _settings(low_volatility_percentile=0.8, high_volatility_percentile=0.8)
