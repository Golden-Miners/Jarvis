import csv
from datetime import datetime
from pathlib import Path

from jarvis.schemas import Candle, SymbolInfo, Tick


class MockProvider:
    """Replay CSV candles and caller-supplied market metadata without broker access."""

    def __init__(
        self,
        fixture_dir: Path,
        symbol_info: dict[str, SymbolInfo] | None = None,
        ticks: dict[str, Tick] | None = None,
    ) -> None:
        self.fixture_dir = fixture_dir
        self.symbol_info = symbol_info or {}
        self.ticks = ticks or {}

    def get_candles(
        self, symbol: str, tf: str, n: int, broker_symbol: str | None = None
    ) -> list[Candle]:
        """Read the newest n fixture candles in ascending timestamp order."""
        if n <= 0:
            raise ValueError("n must be positive")
        path = self.fixture_dir / f"{symbol}_{tf}.csv"
        with path.open(newline="", encoding="utf-8") as stream:
            candles = [self._parse_candle(row) for row in csv.DictReader(stream)]
        candles.sort(key=lambda candle: candle.timestamp)
        return candles[-n:]

    def get_symbol_info(self, symbol: str, broker_symbol: str | None = None) -> SymbolInfo:
        """Return injected metadata or raise when it was not supplied."""
        try:
            return self.symbol_info[symbol]
        except KeyError as exc:
            raise KeyError(f"No symbol info supplied for {symbol}") from exc

    def get_tick(self, symbol: str, broker_symbol: str | None = None) -> Tick:
        """Return an injected tick or raise when it was not supplied."""
        try:
            return self.ticks[symbol]
        except KeyError as exc:
            raise KeyError(f"No tick supplied for {symbol}") from exc

    @staticmethod
    def _parse_candle(row: dict[str, str]) -> Candle:
        return Candle(
            timestamp=datetime.fromisoformat(row["timestamp"]),
            open=float(row["open"]),
            high=float(row["high"]),
            low=float(row["low"]),
            close=float(row["close"]),
            volume=float(row["volume"]),
        )
