from collections.abc import Sequence

from jarvis.schemas import FibonacciLevels


def fibonacci_retracements(
    start_price: float, end_price: float, ratios: Sequence[float]
) -> FibonacciLevels:
    """Return typed Fibonacci retracement prices for explicit anchors."""
    if start_price <= 0 or end_price <= 0:
        raise ValueError("anchor prices must be positive")
    if not ratios or any(ratio < 0 for ratio in ratios):
        raise ValueError("ratios must be nonempty and nonnegative")
    difference = end_price - start_price
    levels = {str(ratio): end_price - difference * ratio for ratio in ratios}
    return FibonacciLevels(start_price=start_price, end_price=end_price, levels=levels)
