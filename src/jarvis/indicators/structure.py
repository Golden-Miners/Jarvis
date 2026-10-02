from collections.abc import Sequence
from typing import Literal

from jarvis.schemas import Candle, StructureBreak, SwingPoint

TrendDirection = Literal["UP", "DOWN", "RANGE"]


def swings(
    candles: Sequence[Candle], left: int, right: int
) -> list[SwingPoint]:
    """Find strict swing highs/lows using explicit left and right widths."""
    if left <= 0 or right <= 0:
        raise ValueError("left and right must be positive")

    points: list[SwingPoint] = []
    for index in range(left, len(candles) - right):
        window = candles[index - left : index + right + 1]
        high = candles[index].high
        low = candles[index].low
        if all(high > item.high for offset, item in enumerate(window) if offset != left):
            points.append(
                SwingPoint(index=index, timestamp=candles[index].timestamp, price=high, kind="HIGH")
            )
        if all(low < item.low for offset, item in enumerate(window) if offset != left):
            points.append(
                SwingPoint(index=index, timestamp=candles[index].timestamp, price=low, kind="LOW")
            )
    return sorted(points, key=lambda point: (point.index, point.kind))


def structure_breaks(
    candles: Sequence[Candle],
    swing_points: Sequence[SwingPoint],
    prior_trend: TrendDirection,
) -> list[StructureBreak]:
    """Find closes crossing the latest confirmed swing and classify BOS/CHoCH."""
    if prior_trend not in ("UP", "DOWN", "RANGE"):
        raise ValueError(f"unsupported prior trend: {prior_trend}")
    if not candles:
        return []

    events: list[StructureBreak] = []
    last_high: SwingPoint | None = None
    last_low: SwingPoint | None = None
    by_index = {point.index: point for point in swing_points}
    for index, candle in enumerate(candles):
        point = by_index.get(index)
        if point is not None:
            if point.kind == "HIGH":
                last_high = point
            else:
                last_low = point
        previous_close = candles[index - 1].close if index else candle.close
        if last_high and previous_close <= last_high.price < candle.close:
            events.append(_break(index, candle, last_high.price, "UP", prior_trend))
            last_high = None
        if last_low and previous_close >= last_low.price > candle.close:
            events.append(_break(index, candle, last_low.price, "DOWN", prior_trend))
            last_low = None
    return events


def _break(
    index: int,
    candle: Candle,
    level: float,
    direction: Literal["UP", "DOWN"],
    prior_trend: TrendDirection,
) -> StructureBreak:
    kind: Literal["BOS", "CHOCH"] = "BOS" if prior_trend == direction else "CHOCH"
    return StructureBreak(
        index=index,
        timestamp=candle.timestamp,
        level=level,
        direction=direction,
        kind=kind,
    )
