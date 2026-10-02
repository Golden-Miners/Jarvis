from collections.abc import Sequence

from jarvis.schemas import Candle, FairValueGap, OrderBlock, PriceZone, SwingPoint


def fair_value_gaps(candles: Sequence[Candle]) -> list[FairValueGap]:
    """Detect three-candle wick gaps between the first and third candles."""
    gaps: list[FairValueGap] = []
    for index in range(2, len(candles)):
        first = candles[index - 2]
        third = candles[index]
        if first.high < third.low:
            gaps.append(
                FairValueGap(
                    start_index=index - 2,
                    end_index=index,
                    lower=first.high,
                    upper=third.low,
                    direction="BULLISH",
                )
            )
        elif first.low > third.high:
            gaps.append(
                FairValueGap(
                    start_index=index - 2,
                    end_index=index,
                    lower=third.high,
                    upper=first.low,
                    direction="BEARISH",
                )
            )
    return gaps


def order_blocks(
    candles: Sequence[Candle], displacement: float
) -> list[OrderBlock]:
    """Find opposite-color candles before closes displaced beyond their range."""
    if displacement <= 0:
        raise ValueError("displacement must be positive")

    blocks: list[OrderBlock] = []
    for index in range(1, len(candles)):
        previous = candles[index - 1]
        current = candles[index]
        move = current.close - current.open
        if move >= displacement and previous.close < previous.open:
            blocks.append(
                OrderBlock(
                    index=index - 1,
                    lower=previous.low,
                    upper=previous.high,
                    direction="BULLISH",
                )
            )
        elif move <= -displacement and previous.close > previous.open:
            blocks.append(
                OrderBlock(
                    index=index - 1,
                    lower=previous.low,
                    upper=previous.high,
                    direction="BEARISH",
                )
            )
    return blocks


def price_zones(swing_points: Sequence[SwingPoint], tolerance: float) -> list[PriceZone]:
    """Group sorted swing prices whose adjacent gaps are within tolerance."""
    if tolerance < 0:
        raise ValueError("tolerance must be nonnegative")
    if not swing_points:
        return []

    prices = sorted(point.price for point in swing_points)
    groups: list[list[float]] = [[prices[0]]]
    for price in prices[1:]:
        if price - groups[-1][-1] <= tolerance:
            groups[-1].append(price)
        else:
            groups.append([price])
    return [
        PriceZone(lower=group[0], upper=group[-1], level_count=len(group))
        for group in groups
    ]

