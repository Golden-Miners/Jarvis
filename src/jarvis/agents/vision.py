from collections.abc import Sequence

from jarvis.config.models import InstrumentConfig
from jarvis.data.provider import DataProvider
from jarvis.schemas import InstrumentMarketData, VisionResult


def run_vision(
    provider: DataProvider,
    instruments: Sequence[InstrumentConfig],
    timeframes: Sequence[str],
    candle_count: int,
) -> VisionResult:
    """Fetch and validate market data for each configured instrument."""
    if candle_count <= 0:
        raise ValueError("candle_count must be positive")
    if not timeframes:
        raise ValueError("at least one timeframe is required")

    results: dict[str, InstrumentMarketData] = {}
    for instrument in instruments:
        candles = {
            timeframe: provider.get_candles(
                instrument.symbol,
                timeframe,
                candle_count,
                instrument.broker_symbol,
            )
            for timeframe in timeframes
        }
        results[instrument.symbol] = InstrumentMarketData(
            symbol=instrument.symbol,
            candles=candles,
            symbol_info=provider.get_symbol_info(
                instrument.symbol, instrument.broker_symbol
            ),
            tick=provider.get_tick(instrument.symbol, instrument.broker_symbol),
        )
    return VisionResult(instruments=results)
