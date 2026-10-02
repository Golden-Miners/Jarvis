from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from jarvis.schemas import Candle, SymbolInfo, Tick

TIMEFRAMES = {
    "M5": "TIMEFRAME_M5",
    "M15": "TIMEFRAME_M15",
    "H1": "TIMEFRAME_H1",
    "H4": "TIMEFRAME_H4",
    "D1": "TIMEFRAME_D1",
}


class MT5Provider:
    """Read market data through the approved MetaTrader5 API calls only."""

    def __init__(
        self,
        cache_dir: Path,
        terminal_path: str | None = None,
        mt5_module: Any | None = None,
    ) -> None:
        self.cache_dir = cache_dir
        self.terminal_path = terminal_path
        self._mt5 = mt5_module

    def initialize(self) -> None:
        """Initialize an MT5 terminal connection or raise with the API error."""
        mt5 = self._module()
        if self.terminal_path:
            initialized = mt5.initialize(path=self.terminal_path)
        else:
            initialized = mt5.initialize()
        if not initialized:
            raise ConnectionError("MetaTrader5 initialize failed")

    def shutdown(self) -> None:
        """Close the MT5 terminal connection if the module was loaded."""
        if self._mt5 is not None:
            self._mt5.shutdown()

    def get_candles(
        self, symbol: str, tf: str, n: int, broker_symbol: str | None = None
    ) -> list[Candle]:
        """Fetch closed candles, validate them, and refresh the parquet cache."""
        if n <= 0:
            raise ValueError("n must be positive")
        mt5 = self._module()
        timeframe_name = TIMEFRAMES.get(tf)
        if timeframe_name is None:
            raise ValueError(f"Unsupported timeframe: {tf}")
        timeframe = getattr(mt5, timeframe_name)
        rates = mt5.copy_rates_from_pos(broker_symbol or symbol, timeframe, 1, n)
        if rates is None:
            raise RuntimeError("copy_rates_from_pos failed")
        candles = [self._candle_from_rate(rate) for rate in rates]
        candles.sort(key=lambda candle: candle.timestamp)
        self._validate_candles(candles)
        self._update_cache(symbol, tf, candles)
        return candles

    def get_symbol_info(self, symbol: str, broker_symbol: str | None = None) -> SymbolInfo:
        """Fetch read-only symbol metadata and map it to the shared schema."""
        mt5 = self._module()
        info = mt5.symbol_info(broker_symbol or symbol)
        if info is None:
            raise LookupError(f"symbol_info returned no metadata for {broker_symbol or symbol}")
        return SymbolInfo(
            symbol=symbol,
            digits=info.digits,
            point=info.point,
            trade_tick_size=info.trade_tick_size,
            trade_tick_value=info.trade_tick_value,
            volume_min=info.volume_min,
            volume_max=info.volume_max,
            volume_step=info.volume_step,
        )

    def get_tick(self, symbol: str, broker_symbol: str | None = None) -> Tick:
        """Fetch and map one read-only bid/ask tick."""
        mt5 = self._module()
        name = broker_symbol or symbol
        tick = mt5.symbol_info_tick(name)
        if tick is None:
            raise LookupError(f"symbol_info_tick returned no tick for {name}")
        return Tick(
            timestamp=datetime.fromtimestamp(tick.time, UTC), bid=tick.bid, ask=tick.ask
        )

    def _module(self) -> Any:
        if self._mt5 is None:
            try:
                import MetaTrader5  # type: ignore[import-untyped]
            except ImportError as exc:
                raise RuntimeError("MetaTrader5 is required on Windows to use MT5Provider") from exc
            self._mt5 = MetaTrader5
        return self._mt5

    @staticmethod
    def _candle_from_rate(rate: Any) -> Candle:
        return Candle(
            timestamp=datetime.fromtimestamp(int(rate["time"]), UTC),
            open=float(rate["open"]),
            high=float(rate["high"]),
            low=float(rate["low"]),
            close=float(rate["close"]),
            volume=float(rate["tick_volume"]),
        )

    @staticmethod
    def _validate_candles(candles: list[Candle]) -> None:
        timestamps = [candle.timestamp for candle in candles]
        if len(timestamps) != len(set(timestamps)):
            raise ValueError("duplicate candle timestamps")
        if timestamps != sorted(timestamps):
            raise ValueError("candles must be chronologically ordered")

    def _update_cache(self, symbol: str, tf: str, candles: list[Candle]) -> None:
        if not candles:
            return
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        path = self.cache_dir / f"{symbol}_{tf}.parquet"
        import pandas as pd  # type: ignore[import-untyped]

        fresh = pd.DataFrame([candle.model_dump() for candle in candles])
        if path.exists():
            cached = pd.read_parquet(path)
            if not cached.empty and cached["timestamp"].max() >= fresh["timestamp"].max():
                return
            combined = pd.concat([cached, fresh], ignore_index=True)
            combined = combined.drop_duplicates(subset=["timestamp"], keep="last")
            combined = combined.sort_values("timestamp")
        else:
            combined = fresh
        temporary_path = path.with_suffix(".parquet.tmp")
        combined.to_parquet(temporary_path, index=False)
        temporary_path.replace(path)
