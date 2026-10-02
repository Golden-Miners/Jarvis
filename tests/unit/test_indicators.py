from datetime import UTC, datetime, timedelta

import pytest

from jarvis.indicators import (
    atr,
    ema,
    fair_value_gaps,
    fibonacci_retracements,
    order_blocks,
    price_zones,
    structure_breaks,
    swings,
)
from jarvis.schemas import Candle, SwingPoint


def _candle(
    index: int,
    open_price: float,
    high: float,
    low: float,
    close: float,
) -> Candle:
    return Candle(
        timestamp=datetime(2026, 1, 1, tzinfo=UTC) + timedelta(minutes=index * 15),
        open=open_price,
        high=high,
        low=low,
        close=close,
        volume=1,
    )


def test_atr_wilder_seed_and_smoothing() -> None:
    candles = [
        _candle(0, 10, 12, 9, 11),
        _candle(1, 11, 13, 10, 12),
        _candle(2, 12, 14, 11, 13),
    ]

    assert atr(candles, 2) == [None, 3.0, 3.0]
    assert atr(candles, 4) == [None, None, None]
    assert atr([], 2) == []
    with pytest.raises(ValueError, match="period must be positive"):
        atr(candles, 0)


def test_ema_uses_explicit_period_and_first_value_seed() -> None:
    assert ema([10, 12, 14], 2) == pytest.approx([10, 11.3333333333, 13.1111111111])
    assert ema([], 3) == []
    with pytest.raises(ValueError, match="period must be positive"):
        ema([1], 0)


def test_swings_identify_strict_high_and_low_pivots() -> None:
    candles = [
        _candle(0, 10, 11, 9, 10),
        _candle(1, 10, 15, 8, 10),
        _candle(2, 10, 12, 7, 10),
        _candle(3, 10, 11, 9, 10),
    ]

    points = swings(candles, left=1, right=1)

    assert [(point.index, point.kind, point.price) for point in points] == [
        (1, "HIGH", 15),
        (2, "LOW", 7),
    ]
    with pytest.raises(ValueError, match="left and right"):
        swings(candles, left=0, right=1)


def test_structure_breaks_classify_bos_and_choch_by_prior_trend() -> None:
    candles = [
        _candle(0, 10, 11, 9, 10),
        _candle(1, 10, 12, 9, 11),
        _candle(2, 11, 13, 10, 12),
        _candle(3, 12, 14, 11, 12.5),
        _candle(4, 12.5, 13, 9, 9.5),
    ]
    points = [
        SwingPoint(index=1, timestamp=candles[1].timestamp, price=12, kind="HIGH"),
        SwingPoint(index=2, timestamp=candles[2].timestamp, price=10, kind="LOW"),
    ]

    bullish = structure_breaks(candles, points, prior_trend="UP")
    bearish = structure_breaks(candles, points, prior_trend="DOWN")

    assert [(item.direction, item.kind) for item in bullish] == [("UP", "BOS"), ("DOWN", "CHOCH")]
    assert [(item.direction, item.kind) for item in bearish] == [("UP", "CHOCH"), ("DOWN", "BOS")]


def test_fair_value_gaps_detect_bullish_and_bearish_three_candle_gaps() -> None:
    bullish = [_candle(0, 10, 11, 9, 10), _candle(1, 12, 13, 12, 12.5), _candle(2, 14, 15, 12, 14)]
    bearish = [_candle(0, 14, 15, 13, 14), _candle(1, 12, 13, 11, 12), _candle(2, 10, 12, 9, 10)]

    assert [(gap.direction, gap.lower, gap.upper) for gap in fair_value_gaps(bullish)] == [
        ("BULLISH", 11, 12)
    ]
    assert [(gap.direction, gap.lower, gap.upper) for gap in fair_value_gaps(bearish)] == [
        ("BEARISH", 12, 13)
    ]
    assert fair_value_gaps(bullish[:2]) == []


def test_order_blocks_require_opposite_color_and_minimum_displacement() -> None:
    candles = [
        _candle(0, 12, 13, 10, 11),
        _candle(1, 11, 15, 11, 14),
        _candle(2, 12, 15, 12, 14),
        _candle(3, 14, 15, 9, 11),
    ]

    blocks = order_blocks(candles, displacement=2)

    assert [(block.index, block.direction) for block in blocks] == [
        (0, "BULLISH"),
        (2, "BEARISH"),
    ]
    with pytest.raises(ValueError, match="displacement must be positive"):
        order_blocks(candles, displacement=0)


def test_price_zones_cluster_nearby_swing_levels() -> None:
    points = [
        SwingPoint(index=0, timestamp=datetime.now(UTC), price=10, kind="LOW"),
        SwingPoint(index=1, timestamp=datetime.now(UTC), price=10.2, kind="HIGH"),
        SwingPoint(index=2, timestamp=datetime.now(UTC), price=12, kind="LOW"),
    ]

    zones = price_zones(points, tolerance=0.25)

    assert [(zone.lower, zone.upper, zone.level_count) for zone in zones] == [
        (10, 10.2, 2),
        (12, 12, 1),
    ]
    with pytest.raises(ValueError, match="tolerance"):
        price_zones(points, tolerance=-1)


def test_fibonacci_retracements_use_explicit_anchors_and_ratios() -> None:
    result = fibonacci_retracements(100, 200, [0, 0.5, 1])

    assert result.levels == {"0": 200, "0.5": 150, "1": 100}
    assert fibonacci_retracements(200, 100, [0.5]).levels == {"0.5": 150}
    with pytest.raises(ValueError, match="ratios"):
        fibonacci_retracements(100, 200, [])
