from __future__ import annotations

from datetime import datetime

from jarvis.indicators import atr, ema
from jarvis.schemas import Candle, SetupCandidate
from jarvis.strategies.base import BaseStrategy
from jarvis.strategies.context import StrategyContext


class BlackWidow(BaseStrategy):
    """Trend-pullback strategy: EMA trend, pullback to EMA, entry on recovery."""

    @property
    def name(self) -> str:
        return "black_widow"

    def analyse(self, ctx: StrategyContext) -> list[SetupCandidate]:
        timeframe, candles = self._primary_window(ctx)
        if timeframe is None or candles is None or len(candles) < 20:
            return []

        ema_period = self._positive_int(self.params.get("ema_period", 20), "ema_period")
        pullback_bars = self._positive_int(
            self.params.get("pullback_bars", 5), "pullback_bars"
        )
        rr_multiple = self._positive_float(self.params.get("rr_multiple", 2.0), "rr_multiple")
        atr_sl_multiple = self._positive_float(
            self.params.get("atr_sl_multiple", 1.5), "atr_sl_multiple"
        )
        displacement = self._positive_float(
            self.params.get("displacement", 0.25), "displacement"
        )
        min_confidence = self._bounded_float(
            self.params.get("min_confidence", 0.55), "min_confidence", 0.0, 1.0
        )

        recent = candles[-40:]
        atr_value = self._latest_atr(recent, 14)
        if atr_value is None or atr_value <= 0:
            return []

        closes = [candle.close for candle in recent]
        ema_values = ema(closes, ema_period)
        ema_line = ema_values[-1]
        if ema_line is None:
            return []

        trend = ctx.market_structure.timeframe_trends.get(timeframe, "RANGE")
        if trend == "RANGE":
            return []

        bullish = self._bullish_setup(
            candles=recent,
            ema_line=ema_line,
            pullback_bars=pullback_bars,
            atr_value=atr_value,
            rr_multiple=rr_multiple,
            atr_sl_multiple=atr_sl_multiple,
            displacement=displacement,
            created_at=ctx.now,
            symbol=ctx.symbol,
        )
        if bullish is not None and bullish.confidence >= min_confidence:
            return [bullish]

        bearish = self._bearish_setup(
            candles=recent,
            ema_line=ema_line,
            pullback_bars=pullback_bars,
            atr_value=atr_value,
            rr_multiple=rr_multiple,
            atr_sl_multiple=atr_sl_multiple,
            displacement=displacement,
            created_at=ctx.now,
            symbol=ctx.symbol,
        )
        if bearish is not None and bearish.confidence >= min_confidence:
            return [bearish]
        return []

    def _bullish_setup(
        self,
        candles: list[Candle],
        ema_line: float,
        pullback_bars: int,
        atr_value: float,
        rr_multiple: float,
        atr_sl_multiple: float,
        displacement: float,
        created_at: datetime,
        symbol: str,
    ) -> SetupCandidate | None:
        pullback = candles[-pullback_bars:]
        last = candles[-1]
        prev = candles[-2]

        price_below_or_at_ema = last.close <= ema_line
        ema_touch_in_pullback = any(
            candle.low <= ema_line <= candle.high for candle in pullback[:-1]
        )
        if not (price_below_or_at_ema and ema_touch_in_pullback):
            return None

        if not (last.close > prev.close and last.close > last.open):
            return None

        entry = last.close
        sl = min(candle.low for candle in pullback)
        sl_distance = entry - sl
        if sl_distance <= 0:
            return None
        tp = entry + sl_distance * rr_multiple
        confidence = min(0.6 + (last.close - last.open) / max(atr_value, 1e-9) * 0.3, 0.95)
        evidence = [
            f"bullish pullback to EMA {ema_line:.2f}",
            f"recovery candle close {entry:.2f}",
            f"SL {sl:.2f} TP {tp:.2f}",
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

    def _bearish_setup(
        self,
        candles: list[Candle],
        ema_line: float,
        pullback_bars: int,
        atr_value: float,
        rr_multiple: float,
        atr_sl_multiple: float,
        displacement: float,
        created_at: datetime,
        symbol: str,
    ) -> SetupCandidate | None:
        pullback = candles[-pullback_bars:]
        last = candles[-1]
        prev = candles[-2]

        price_above_or_at_ema = last.close >= ema_line
        ema_touch_in_pullback = any(
            candle.high >= ema_line >= candle.low for candle in pullback[:-1]
        )
        if not (price_above_or_at_ema and ema_touch_in_pullback):
            return None

        if not (last.close < prev.close and last.close < last.open):
            return None

        entry = last.close
        sl = max(candle.high for candle in pullback)
        sl_distance = sl - entry
        if sl_distance <= 0:
            return None
        tp = entry - sl_distance * rr_multiple
        confidence = min(0.6 + (last.open - last.close) / max(atr_value, 1e-9) * 0.3, 0.95)
        evidence = [
            f"bearish pullback to EMA {ema_line:.2f}",
            f"recovery candle close {entry:.2f}",
            f"SL {sl:.2f} TP {tp:.2f}",
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
        atr_values = atr(candles, period)
        values = [value for value in atr_values if value is not None]
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