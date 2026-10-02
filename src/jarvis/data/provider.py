from typing import Protocol

from jarvis.schemas import Candle, SymbolInfo, Tick


class DataProvider(Protocol):
    """Read-only interface for market data providers."""

    def get_candles(self, symbol: str, tf: str, n: int) -> list[Candle]:
        """Return up to n candles in ascending timestamp order."""

    def get_symbol_info(self, symbol: str) -> SymbolInfo:
        """Return explicit metadata for a symbol."""

    def get_tick(self, symbol: str) -> Tick:
        """Return the latest explicit tick for a symbol."""
