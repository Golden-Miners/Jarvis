"""Tests for Quicksilver (TimesFM forecast) agent."""

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

pytestmark = pytest.mark.slow

from jarvis.agents.quicksilver import (
    QuicksilverSettings,
    TimesFMSingleton,
    _extract_quantiles,
    run_quicksilver,
)
from jarvis.schemas import Candle


def _make_candles(n: int, base: float = 2000.0) -> list[Candle]:
    """Create n synthetic candles with a mild uptrend."""
    candles = []
    for i in range(n):
        close = base + i * 0.5
        candles.append(Candle(
            timestamp=datetime(2024, 1, 1, tzinfo=UTC),
            open=close - 0.1,
            high=close + 0.2,
            low=close - 0.3,
            close=close,
            volume=100,
        ))
    return candles


def _make_mock_model(
    points: np.ndarray,
    quantiles: np.ndarray,
) -> MagicMock:
    """Build a mock TimesFM model returning the given arrays."""
    mock = MagicMock()
    mock.forecast_config = MagicMock()
    mock.forecast.return_value = (points, quantiles)
    return mock


class TestExtractQuantiles:
    """Unit tests for the quantile extraction helper."""

    def test_extracts_all_three_quantiles(self) -> None:
        point = np.array([1.0, 2.0, 3.0])
        quant = np.array([
            [0.5, 1.0, 1.5],
            [1.5, 2.0, 2.5],
            [2.5, 3.0, 3.5],
        ])
        median, q10, q90 = _extract_quantiles(point, quant)
        assert median == [1.0, 2.0, 3.0]
        assert q10 == [0.5, 1.5, 2.5]
        assert q90 == [1.5, 2.5, 3.5]

    def test_falls_back_to_point_if_1d(self) -> None:
        point = np.array([1.0, 2.0])
        quant = np.array([10.0, 20.0])  # 1-D
        median, q10, q90 = _extract_quantiles(point, quant)
        assert median == [1.0, 2.0]
        assert q10 == []
        assert q90 == []


class TestRunQuicksilver:
    """Unit tests for the run_quicksilver function."""

    def test_returns_none_when_insufficient_candles(self) -> None:
        settings = QuicksilverSettings(context_len=512)
        result = run_quicksilver(
            symbol="XAUUSD",
            timeframe="M15",
            candles=_make_candles(100),
            atr=5.0,
            settings=settings,
        )
        assert result is None

    @patch.object(TimesFMSingleton, "get_model", return_value=None)
    def test_returns_none_when_model_unavailable(
        self, mock_get: MagicMock,
    ) -> None:
        settings = QuicksilverSettings(context_len=10)
        result = run_quicksilver(
            symbol="XAUUSD",
            timeframe="M15",
            candles=_make_candles(20),
            atr=5.0,
            settings=settings,
        )
        assert result is None

    def test_returns_forecast_with_mock_model(self) -> None:
        settings = QuicksilverSettings(
            context_len=10, horizon_bars=5,
        )
        points = np.array([
            [2010.0, 2011.0, 2012.0, 2013.0, 2014.0],
        ])
        quantiles = np.array([[
            [2008.0, 2010.0, 2012.0],
            [2009.0, 2011.0, 2013.0],
            [2010.0, 2012.0, 2014.0],
            [2011.0, 2013.0, 2015.0],
            [2012.0, 2014.0, 2016.0],
        ]])
        mock = _make_mock_model(points, quantiles)

        with patch.object(
            TimesFMSingleton, "get_model", return_value=mock,
        ):
            result = run_quicksilver(
                symbol="XAUUSD",
                timeframe="M15",
                candles=_make_candles(20, base=2000.0),
                atr=5.0,
                settings=settings,
            )

        assert result is not None
        assert result.symbol == "XAUUSD"
        assert result.timeframe == "M15"
        assert result.horizon_bars == 5
        assert len(result.median) == 5
        assert len(result.q10) == 5
        assert len(result.q90) == 5
        assert result.expected_direction in (
            "UP", "DOWN", "FLAT",
        )
        assert 0.0 <= result.strength <= 1.0

    def test_bullish_direction_when_drift_positive(self) -> None:
        settings = QuicksilverSettings(
            context_len=10, horizon_bars=3,
        )
        # Last close of 20 candles (base=2000, step=0.5):
        # candles[-10:] → closes 2005..2009.5
        # Last close used = 2009.5
        points = np.array([[2015.0, 2017.0, 2020.0]])
        quantiles = np.array([[
            [2013.0, 2015.0, 2017.0],
            [2015.0, 2017.0, 2019.0],
            [2018.0, 2020.0, 2022.0],
        ]])
        mock = _make_mock_model(points, quantiles)

        with patch.object(
            TimesFMSingleton, "get_model", return_value=mock,
        ):
            result = run_quicksilver(
                symbol="XAUUSD",
                timeframe="M15",
                candles=_make_candles(20),
                atr=5.0,
                settings=settings,
            )
        assert result is not None
        assert result.expected_direction == "UP"
        assert result.strength > 0

    def test_bearish_direction_when_drift_negative(self) -> None:
        settings = QuicksilverSettings(
            context_len=10, horizon_bars=3,
        )
        points = np.array([[1995.0, 1992.0, 1990.0]])
        quantiles = np.array([[
            [1993.0, 1995.0, 1997.0],
            [1990.0, 1992.0, 1994.0],
            [1988.0, 1990.0, 1992.0],
        ]])
        mock = _make_mock_model(points, quantiles)

        with patch.object(
            TimesFMSingleton, "get_model", return_value=mock,
        ):
            result = run_quicksilver(
                symbol="XAUUSD",
                timeframe="M15",
                candles=_make_candles(20),
                atr=5.0,
                settings=settings,
            )
        assert result is not None
        assert result.expected_direction == "DOWN"

    def test_flat_direction_when_small_drift(self) -> None:
        settings = QuicksilverSettings(
            context_len=10, horizon_bars=3,
        )
        # Last close = 2009.5, endpoint median = 2010.0
        # drift = 0.5, atr = 5 → FLAT
        points = np.array([[2009.6, 2009.8, 2010.0]])
        quantiles = np.array([[
            [2009.0, 2009.6, 2010.2],
            [2009.2, 2009.8, 2010.4],
            [2009.4, 2010.0, 2010.6],
        ]])
        mock = _make_mock_model(points, quantiles)

        with patch.object(
            TimesFMSingleton, "get_model", return_value=mock,
        ):
            result = run_quicksilver(
                symbol="XAUUSD",
                timeframe="M15",
                candles=_make_candles(20),
                atr=5.0,
                settings=settings,
            )
        assert result is not None
        assert result.expected_direction == "FLAT"

    def test_strength_clipped_at_one(self) -> None:
        settings = QuicksilverSettings(
            context_len=10, horizon_bars=3,
        )
        # Last close = 2009.5, endpoint median = 2100
        # drift = 90.5, atr = 1 → 90.5 clipped to 1.0
        points = np.array([[2050.0, 2075.0, 2100.0]])
        quantiles = np.array([[
            [2048.0, 2050.0, 2052.0],
            [2073.0, 2075.0, 2077.0],
            [2098.0, 2100.0, 2102.0],
        ]])
        mock = _make_mock_model(points, quantiles)

        with patch.object(
            TimesFMSingleton, "get_model", return_value=mock,
        ):
            result = run_quicksilver(
                symbol="XAUUSD",
                timeframe="M15",
                candles=_make_candles(20),
                atr=1.0,
                settings=settings,
            )
        assert result is not None
        assert result.strength == 1.0
