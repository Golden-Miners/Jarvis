from __future__ import annotations

from datetime import datetime

from jarvis.indicators import atr, swings
from jarvis.schemas import Candle, SetupCandidate
from jarvis.strategies.base import BaseStrategy
from jarvis.strategies.context import StrategyContext


class Falcon(BaseStrategy):
    """Breakout strategy: price closes beyond recent swing extreme with momentum."""

    @property
    def name(self) -> str:
        return "falcon"

    def analyse(self, ctx: StrategyContext) -> list[SetupCandidate]:
        timeframe, candles = self._primary_window(ctx)
        if timeframe is None or candles is None or len(candles) < 20:
            return []

        lookback = self._positive_int(self.params.get("lookback", 20), "lookback")
        atr_period = self._positive_int(self.params.get("atr_period", 14), "atr_period")
        rr_multiple = self._positive_float(self.params.get("rr_multiple", 2.0), "rr_multiple")
        atr_sl_multiple = self._positive_float(
            self.params.get("atr_sl_multiple", 1.5), "atr_sl_multiple"
        )
        breakout_distance = self._positive_float(
            self.params.get("breakout_distance", 0.5), "breakout_distance"
        )
        min_confidence = self._bounded_float(
            self.params.get("min_confidence", 0.55), "min_confidence", 0.0, 1.0
        )

        recent = candles[-lookback:]
        atr_value = self._latest_atr(recent, atr_period)
        if atr_value is None or atr_value <= 0:
            return []

        trend = ctx.market_structure.timeframe_trends.get(timeframe, "RANGE")
        if trend == "RANGE":
            return []

        last = candles[-1]
        prev = candles[-2]
        prior = recent[:-1]
        swing_points = swings(prior, left=5, right=5)
        if not swing_points:
            swing_points = swings(prior, left=3, right=3)
        highs = [point.price for point in swing_points if point.kind == "HIGH"]
        lows = [point.price for point in swing_points if point.kind == "LOW"]
        recent_high = max(highs) if highs else max(candle.high for candle in prior)
        recent_low = min(lows) if lows else min(candle.low for candle in prior)

        bullish = self._bullish_setup(
            trend=trend,
            last=last,
            prev=prev,
            recent_high=recent_high,
            breakout_distance=breakout_distance,
            atr_value=atr_value,
            rr_multiple=rr_multiple,
            atr_sl_multiple=atr_sl_multiple,
            created_at=ctx.now,
            symbol=ctx.symbol,
        )
        if bullish is not None and bullish.confidence >= min_confidence:
            return [bullish]

        bearish = self._bearish_setup(
            trend=trend,
            last=last,
            prev=prev,
            recent_low=recent_low,
            breakout_distance=breakout_distance,
            atr_value=atr_value,
            rr_multiple=rr_multiple,
            atr_sl_multiple=atr_sl_multiple,
            created_at=ctx.now,
            symbol=ctx.symbol,
        )
        if bearish is not None and bearish.confidence >= min_confidence:
            return [bearish]
        return []

    def _bullish_setup(
        self,
        trend: str,
        last: Candle,
        prev: Candle,
        recent_high: float,
        breakout_distance: float,
        atr_value: float,
        rr_multiple: float,
        atr_sl_multiple: float,
        created_at: datetime,
        symbol: str,
    ) -> SetupCandidate | None:
        if trend != "UP":
            return None
        if not (last.close > last.open and last.close > prev.close):
            return None
        breakout_threshold = recent_high + breakout_distance
        if last.close < breakout_threshold:
            return None
        entry = last.close
        sl = min(prev.low, last.low)
        sl_distance = entry - sl
        if sl_distance <= 0:
            return None
        tp = entry + sl_distance * rr_multiple
        body = last.close - last.open
        confidence = min(0.6 + body / max(atr_value, 1e-9) * 0.3, 0.95)
        evidence = [
            f"bullish breakout above swing high {recent_high:.2f}",
            f"entry {entry:.2f} SL {sl:.2f} TP {tp:.2f}",
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
        trend: str,
        last: Candle,
        prev: Candle,
        recent_low: float,
        breakout_distance: float,
        atr_value: float,
        rr_multiple: float,
        atr_sl_multiple: float,
        created_at: datetime,
        symbol: str,
    ) -> SetupCandidate | None:
        if trend != "DOWN":
            return None
        if not (last.close < last.open and last.close < prev.close):
            return None
        breakout_threshold = recent_low - breakout_distance
        if last.close > breakout_threshold:
            return None
        entry = last.close
        sl = max(prev.high, last.high)
        sl_distance = sl - entry
        if sl_distance <= 0:
            return None
        tp = entry - sl_distance * rr_multiple
        body = last.open - last.close
        confidence = min(0.6 + body / max(atr_value, 1e-9) * 0.3, 0.95)
        evidence = [
            f"bearish breakout below swing low {recent_low:.2f}",
            f"entry {entry:.2f} SL {sl:.2f} TP {tp:.2f}",
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
        values: list[float] = [value for value in atr_values if value is not None]
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