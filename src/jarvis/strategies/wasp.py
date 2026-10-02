from __future__ import annotations

from datetime import datetime

from jarvis.indicators import atr, fibonacci_retracements, price_zones, swings
from jarvis.schemas import Candle, SetupCandidate
from jarvis.strategies.base import BaseStrategy
from jarvis.strategies.context import StrategyContext


class Wasp(BaseStrategy):
    """Supply-demand + Fib confluence strategy.

    Detects major swings to establish Fibonacci retracements.
    Finds historical price zones (supply/demand).
    Fires when price retests a zone that is confluent with a key Fib level.
    Disabled in RANGE trend.
    """

    @property
    def name(self) -> str:
        return "wasp"

    def analyse(self, ctx: StrategyContext) -> list[SetupCandidate]:
        timeframe, candles = self._primary_window(ctx)
        if timeframe is None or candles is None or len(candles) < 50:
            return []

        trend = ctx.market_structure.timeframe_trends.get(timeframe, "RANGE")
        if trend == "RANGE":
            return []

        # Parse params
        swings_left = self._positive_int(self.params.get("swings_left", 5), "swings_left")
        swings_right = self._positive_int(self.params.get("swings_right", 5), "swings_right")
        atr_period = self._positive_int(self.params.get("atr_period", 14), "atr_period")
        zone_atr_tolerance = self._positive_float(
            self.params.get("zone_atr_tolerance", 0.5), "zone_atr_tolerance"
        )
        conf_atr_tolerance = self._positive_float(
            self.params.get("conf_atr_tolerance", 0.2), "conf_atr_tolerance"
        )
        rr_multiple = self._positive_float(self.params.get("rr_multiple", 2.0), "rr_multiple")
        min_confidence = self._bounded_float(
            self.params.get("min_confidence", 0.5), "min_confidence", 0.0, 1.0
        )
        ratios_param = self.params.get("fib_ratios", [0.382, 0.5, 0.618, 0.786])
        if not isinstance(ratios_param, list):
            raise ValueError("fib_ratios must be a list of floats")
        fib_ratios = [float(r) for r in ratios_param]

        # Calculate ATR
        recent = candles[-100:]
        atr_val = self._latest_atr(recent, atr_period)
        if atr_val is None or atr_val <= 0:
            return []

        # Find Swings
        pts = swings(recent, left=swings_left, right=swings_right)
        if len(pts) < 2:
            return []

        # Establish main anchor points based on trend
        start_price, end_price = self._find_anchors(pts, trend)
        if start_price is None or end_price is None or abs(start_price - end_price) < atr_val:
            return []

        # Calculate Fibs
        fibs = fibonacci_retracements(start_price, end_price, fib_ratios)

        # Calculate Zones
        tolerance = zone_atr_tolerance * atr_val
        zones = price_zones(pts, tolerance)
        if not zones:
            return []

        # Find Confluent Zones
        conf_tolerance = conf_atr_tolerance * atr_val
        confluences = []
        for zone in zones:
            for ratio_str, level in fibs.levels.items():
                # A zone spans from lower to upper. Does the level fall in or near the zone?
                if (zone.lower - conf_tolerance) <= level <= (zone.upper + conf_tolerance):
                    confluences.append((zone, ratio_str, level))

        if not confluences:
            return []

        last = recent[-1]
        prev = recent[-2]

        # Look for entry setups
        if trend == "UP":
            setup = self._bullish_setup(
                last, prev, confluences, atr_val, rr_multiple, min_confidence, ctx
            )
            if setup:
                return [setup]
        elif trend == "DOWN":
            setup = self._bearish_setup(
                last, prev, confluences, atr_val, rr_multiple, min_confidence, ctx
            )
            if setup:
                return [setup]

        return []

    def _find_anchors(
        self, pts: list, trend: str
    ) -> tuple[float | None, float | None]:
        """Find the absolute high and low of the recent swings to draw Fibs."""
        if not pts:
            return None, None
        highs = [p.price for p in pts if p.kind == "HIGH"]
        lows = [p.price for p in pts if p.kind == "LOW"]
        if not highs or not lows:
            return None, None
        highest = max(highs)
        lowest = min(lows)
        if trend == "UP":
            # UP trend: Fib from bottom to top
            return lowest, highest
        elif trend == "DOWN":
            # DOWN trend: Fib from top to bottom
            return highest, lowest
        return None, None

    def _bullish_setup(
        self,
        last: Candle,
        prev: Candle,
        confluences: list,
        atr_val: float,
        rr_multiple: float,
        min_confidence: float,
        ctx: StrategyContext,
    ) -> SetupCandidate | None:
        """BUY if price bounces off a confluent support zone."""
        # Must be a bullish reversal or strong continuation
        if last.close <= last.open or last.close <= prev.close:
            return None

        # Check if the candle low touched or came near a confluent zone
        touch_tolerance = atr_val * 0.2
        valid_conf = None
        for zone, ratio, level in confluences:
            # We want price to have tested the zone (low <= upper) and closed above it (close > lower)
            if last.low <= zone.upper + touch_tolerance and last.close > zone.lower:
                valid_conf = (zone, ratio, level)
                break

        if not valid_conf:
            return None
        
        zone, ratio, level = valid_conf
        entry = last.close
        sl = min(last.low, zone.lower) - atr_val * 0.5
        sl_distance = entry - sl
        if sl_distance <= 0:
            return None
        tp = entry + sl_distance * rr_multiple
        
        confidence = min(0.6 + zone.level_count * 0.05, 0.95)
        if confidence < min_confidence:
            return None

        evidence = [
            f"bullish zone retest: bounce off {zone.lower:.4g}-{zone.upper:.4g}",
            f"confluence with Fib {ratio} ({level:.4g}); SL {sl:.4g} TP {tp:.4g}",
        ]
        return SetupCandidate(
            symbol=ctx.symbol,
            strategy=self.name,
            agent=self.name,
            direction="BUY",
            entry=entry,
            sl=sl,
            tp=tp,
            confidence=confidence,
            evidence=evidence,
            created_at=ctx.now,
        )

    def _bearish_setup(
        self,
        last: Candle,
        prev: Candle,
        confluences: list,
        atr_val: float,
        rr_multiple: float,
        min_confidence: float,
        ctx: StrategyContext,
    ) -> SetupCandidate | None:
        """SELL if price rejects off a confluent resistance zone."""
        # Must be a bearish reversal
        if last.close >= last.open or last.close >= prev.close:
            return None

        # Check if candle high touched or came near a confluent zone
        touch_tolerance = atr_val * 0.2
        valid_conf = None
        for zone, ratio, level in confluences:
            # We want price to have tested the zone (high >= lower) and closed below it (close < upper)
            if last.high >= zone.lower - touch_tolerance and last.close < zone.upper:
                valid_conf = (zone, ratio, level)
                break

        if not valid_conf:
            return None
        
        zone, ratio, level = valid_conf
        entry = last.close
        sl = max(last.high, zone.upper) + atr_val * 0.5
        sl_distance = sl - entry
        if sl_distance <= 0:
            return None
        tp = entry - sl_distance * rr_multiple
        
        confidence = min(0.6 + zone.level_count * 0.05, 0.95)
        if confidence < min_confidence:
            return None

        evidence = [
            f"bearish zone retest: reject off {zone.lower:.4g}-{zone.upper:.4g}",
            f"confluence with Fib {ratio} ({level:.4g}); SL {sl:.4g} TP {tp:.4g}",
        ]
        return SetupCandidate(
            symbol=ctx.symbol,
            strategy=self.name,
            agent=self.name,
            direction="SELL",
            entry=entry,
            sl=sl,
            tp=tp,
            confidence=confidence,
            evidence=evidence,
            created_at=ctx.now,
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
            except ValueError:
                raise ValueError(f"{field} must be a positive integer")
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
            except ValueError:
                raise ValueError(f"{field} must be a positive number")
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
            except ValueError:
                raise ValueError(f"{field} must be between {lower} and {upper}")
        else:
            raise ValueError(f"{field} must be between {lower} and {upper}")
        if not lower <= number <= upper:
            raise ValueError(f"{field} must be between {lower} and {upper}")
        return number
