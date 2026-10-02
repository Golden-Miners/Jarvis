from typing import Protocol

from jarvis.schemas import Candle, SymbolInfo, Tick


class DataProvider(Protocol):
    """Read-only interface for market data providers."""

    def get_candles(
        self, symbol: str, tf: str, n: int, broker_symbol: str | None = None
    ) -> list[Candle]:
        """Return up to n candles in ascending timestamp order."""

    def get_symbol_info(self, symbol: str, broker_symbol: str | None = None) -> SymbolInfo:
        """Return explicit metadata for a symbol."""

    def get_tick(self, symbol: str, broker_symbol: str | None = None) -> Tick:
        """Return the latest explicit tick for a symbol."""
