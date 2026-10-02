from __future__ import annotations

from datetime import datetime

from jarvis.indicators import atr, ema
from jarvis.schemas import Candle, SetupCandidate
from jarvis.strategies.base import BaseStrategy
from jarvis.strategies.context import StrategyContext


class AntMan(BaseStrategy):
    """Mean-reversion strategy: price extended from EMA in RANGE regime → revert to EMA.

    Disabled in UP/DOWN trend — only fires in RANGE volatility regime.
    Entry against the extension; SL beyond the swing extreme; TP at EMA.
    """

    @property
    def name(self) -> str:
        return "ant_man"

    def analyse(self, ctx: StrategyContext) -> list[SetupCandidate]:
        """Return a reversion setup when price is overextended in a ranging market."""
        timeframe, candles = self._primary_window(ctx)
        if timeframe is None or candles is None or len(candles) < 20:
            return []

        # RANGE regime required; skip in strong trend
        if ctx.market_structure.volatility_regime != "NORMAL":
            trend = ctx.market_structure.timeframe_trends.get(timeframe, "RANGE")
            if trend != "RANGE":
                return []
        trend = ctx.market_structure.timeframe_trends.get(timeframe, "RANGE")
        if trend != "RANGE":
            return []

        ema_period = self._positive_int(self.params.get("ema_period", 20), "ema_period")
        atr_period = self._positive_int(self.params.get("atr_period", 14), "atr_period")
        extension_atr = self._positive_float(
            self.params.get("extension_atr", 1.5), "extension_atr"
        )
        rr_multiple = self._positive_float(self.params.get("rr_multiple", 1.5), "rr_multiple")
        min_confidence = self._bounded_float(
            self.params.get("min_confidence", 0.55), "min_confidence", 0.0, 1.0
        )

        recent = candles[-40:]
        atr_value = self._latest_atr(recent, atr_period)
        if atr_value is None or atr_value <= 0:
            return []

        closes = [candle.close for candle in recent]
        ema_values = ema(closes, ema_period)
        ema_line = ema_values[-1]

        last = recent[-1]
        prev = recent[-2]

        bullish = self._bullish_reversion(
            last=last,
            prev=prev,
            ema_line=ema_line,
            atr_value=atr_value,
            extension_atr=extension_atr,
            rr_multiple=rr_multiple,
            created_at=ctx.now,
            symbol=ctx.symbol,
        )
        if bullish is not None and bullish.confidence >= min_confidence:
            return [bullish]

        bearish = self._bearish_reversion(
            last=last,
            prev=prev,
            ema_line=ema_line,
            atr_value=atr_value,
            extension_atr=extension_atr,
            rr_multiple=rr_multiple,
            created_at=ctx.now,
            symbol=ctx.symbol,
        )
        if bearish is not None and bearish.confidence >= min_confidence:
            return [bearish]
        return []

    def _bullish_reversion(
        self,
        last: Candle,
        prev: Candle,
        ema_line: float,
        atr_value: float,
        extension_atr: float,
        rr_multiple: float,
        created_at: datetime,
        symbol: str,
    ) -> SetupCandidate | None:
        """BUY when price has extended far below EMA and prints a recovery close."""
        # Price must be below EMA by at least extension_atr * ATR
        if last.close >= ema_line:
            return None
        gap = ema_line - last.close
        if gap < extension_atr * atr_value:
            return None
        # Recovery signal: current bar closes higher than previous
        if last.close <= prev.close:
            return None
        # Current bar must be bullish (close > open)
        if last.close <= last.open:
            return None

        entry = last.close
        sl = last.low - atr_value * 0.5  # below bar low
        sl_distance = entry - sl
        if sl_distance <= 0:
            return None
        tp = entry + sl_distance * rr_multiple
        # TP must not overshoot EMA for a true reversion trade
        tp = min(tp, ema_line + atr_value * 0.25)
        if tp <= entry:
            return None

        overextension_ratio = gap / atr_value
        confidence = min(0.55 + overextension_ratio * 0.1, 0.90)
        evidence = [
            f"bullish mean reversion: close {last.close:.4g} below EMA {ema_line:.4g}",
            f"gap={gap:.3g} ({overextension_ratio:.1f}x ATR) e={entry:.4g} sl={sl:.4g} tp={tp:.4g}",
        ]
        return SetupCandidate(
            symbol=symbol,
            strategy=self.name,
            agent=self.name,
            direction="BUY",
            entry=entry,
            sl=sl,
            tp=tp,
            confidence=confidence,
            evidence=evidence,
            created_at=created_at,
        )

    def _bearish_reversion(
        self,
        last: Candle,
        prev: Candle,
        ema_line: float,
        atr_value: float,
        extension_atr: float,
        rr_multiple: float,
        created_at: datetime,
        symbol: str,
    ) -> SetupCandidate | None:
        """SELL when price has extended far above EMA and prints a rejection close."""
        # Price must be above EMA by at least extension_atr * ATR
        if last.close <= ema_line:
            return None
        gap = last.close - ema_line
        if gap < extension_atr * atr_value:
            return None
        # Rejection signal: current bar closes lower than previous
        if last.close >= prev.close:
            return None
        # Current bar must be bearish (close < open)
        if last.close >= last.open:
            return None

        entry = last.close
        sl = last.high + atr_value * 0.5  # above bar high
        sl_distance = sl - entry
        if sl_distance <= 0:
            return None
        tp = entry - sl_distance * rr_multiple
        # TP must not overshoot EMA
        tp = max(tp, ema_line - atr_value * 0.25)
        if tp >= entry:
            return None

        overextension_ratio = gap / atr_value
        confidence = min(0.55 + overextension_ratio * 0.1, 0.90)
        evidence = [
            f"bearish mean reversion: close {last.close:.4g} above EMA {ema_line:.4g}",
            f"gap={gap:.3g} ({overextension_ratio:.1f}x ATR) e={entry:.4g} sl={sl:.4g} tp={tp:.4g}",
        ]
        return SetupCandidate(
            symbol=symbol,
            strategy=self.name,
            agent=self.name,
            direction="SELL",
            entry=entry,
            sl=sl,
            tp=tp,
            confidence=confidence,
            evidence=evidence,
            created_at=created_at,
        )

    def _primary_window(
        self, ctx: StrategyContext
    ) -> tuple[str | None, list[Candle] | None]:
        """Return the best available timeframe and its candle list."""
        if not ctx.candles:
            return None, None
        for timeframe in ("M15", "H1", "M5", "H4", "D1"):
            candles = ctx.candles.get(timeframe)
            if candles:
                return timeframe, candles
        for timeframe, candles in ctx.candles.items():
            if candles:
                return timeframe, candles
        return None, None

    def _latest_atr(self, candles: list[Candle], period: int) -> float | None:
        """Return the latest valid ATR value or None."""
        atr_values = atr(candles, period)
        values: list[float] = [v for v in atr_values if v is not None]
        return values[-1] if values else None

    @staticmethod
    def _positive_int(value: object, field: str) -> int:
        if isinstance(value, bool):
            raise ValueError(f"{field} must be a positive integer")
        if isinstance(value, int):
            number = value
        elif isinstance(value, float):
            number = int(value)
        elif isinstance(value, str):
            try:
                number = int(value)
            except ValueError as exc:
                raise ValueError(f"{field} must be a positive integer") from exc
        else:
            raise ValueError(f"{field} must be a positive integer")
        if number <= 0:
            raise ValueError(f"{field} must be positive")
        return number

    @staticmethod
    def _positive_float(value: object, field: str) -> float:
        if isinstance(value, bool):
            raise ValueError(f"{field} must be a positive number")
        if isinstance(value, (int, float)):
            number = float(value)
        elif isinstance(value, str):
            try:
                number = float(value)
            except ValueError as exc:
                raise ValueError(f"{field} must be a positive number") from exc
        else:
            raise ValueError(f"{field} must be a positive number")
        if number <= 0:
            raise ValueError(f"{field} must be positive")
        return number

    @staticmethod
    def _bounded_float(value: object, field: str, lower: float, upper: float) -> float:
        if isinstance(value, bool):
            raise ValueError(f"{field} must be between {lower} and {upper}")
        if isinstance(value, (int, float)):
            number = float(value)
        elif isinstance(value, str):
            try:
                number = float(value)
            except ValueError as exc:
                raise ValueError(f"{field} must be between {lower} and {upper}") from exc
        else:
            raise ValueError(f"{field} must be between {lower} and {upper}")
        if not lower <= number <= upper:
            raise ValueError(f"{field} must be between {lower} and {upper}")
        return number
