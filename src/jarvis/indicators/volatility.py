from collections.abc import Sequence

from jarvis.schemas import Candle


def atr(candles: Sequence[Candle], period: int) -> list[float | None]:
    """Calculate Wilder-smoothed ATR aligned to the input candles."""
    if period <= 0:
        raise ValueError("period must be positive")
    if not candles:
        return []

    true_ranges: list[float] = []
    for index, candle in enumerate(candles):
        previous_close = candles[index - 1].close if index else candle.close
        true_ranges.append(
            max(
                candle.high - candle.low,
                abs(candle.high - previous_close),
                abs(candle.low - previous_close),
            )
        )

    result: list[float | None] = [None] * len(candles)
    if len(candles) < period:
        return result
    result[period - 1] = sum(true_ranges[:period]) / period
    for index in range(period, len(candles)):
        previous_atr = result[index - 1]
        assert previous_atr is not None
        result[index] = (previous_atr * (period - 1) + true_ranges[index]) / period
    return result


def ema(values: Sequence[float], period: int) -> list[float]:
    """Calculate an EMA seeded with the first value and aligned to input."""
    if period <= 0:
        raise ValueError("period must be positive")
    if not values:
        return []

    multiplier = 2.0 / (period + 1)
    result = [values[0]]
    for value in values[1:]:
        result.append((value - result[-1]) * multiplier + result[-1])
    return result
