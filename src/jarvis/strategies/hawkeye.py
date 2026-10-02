from __future__ import annotations

from datetime import datetime
from typing import Any, cast

from jarvis.indicators import atr, fair_value_gaps, order_blocks
from jarvis.schemas import Candle, SetupCandidate
from jarvis.strategies.base import BaseStrategy
from jarvis.strategies.context import StrategyContext


class Hawkeye(BaseStrategy):
    """SMC/ICT strategy that favors FVGs and order blocks in trend alignment."""

    @property
    def name(self) -> str:
        return "hawkeye"

    def analyse(self, ctx: StrategyContext) -> list[SetupCandidate]:
        timeframe, candles = self._primary_window(ctx)
        if timeframe is None or candles is None or len(candles) < 20:
            return []

        lookback = self._positive_int(self.params.get("lookback", 40), "lookback")
        atr_period = self._positive_int(self.params.get("atr_period", 14), "atr_period")
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

        recent = candles[-lookback:]
        atr_value = self._latest_atr(recent, atr_period)
        if atr_value is None or atr_value <= 0:
            return []

        trend = ctx.market_structure.timeframe_trends.get(timeframe, "RANGE")
        gaps = fair_value_gaps(recent)
        blocks = order_blocks(recent, displacement=displacement)
        support = self._nearest_level(ctx.market_structure.key_levels, recent[-1].close, "support")
        resistance = self._nearest_level(
            ctx.market_structure.key_levels, recent[-1].close, "resistance"
        )
        recent_low = min(candle.low for candle in recent)
        recent_high = max(candle.high for candle in recent)

        bullish = self._bullish_setup(
            trend=trend,
            gaps=gaps,
            blocks=blocks,
            support=support,
            recent_low=recent_low,
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
            gaps=gaps,
            blocks=blocks,
            resistance=resistance,
            recent_high=recent_high,
            atr_value=atr_value,
            rr_multiple=rr_multiple,
            atr_sl_multiple=atr_sl_multiple,
            created_at=ctx.now,
            symbol=ctx.symbol,
        )
        if bearish is not None and bearish.confidence >= min_confidence:
            return [bearish]
        return []

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
        series = atr(candles, period)
        for value in reversed(series):
            if value is not None:
                return float(value)
        return None

    def _bullish_setup(
        self,
        *,
        trend: str,
        gaps: list[Any],
        blocks: list[Any],
        support: float | None,
        recent_low: float,
        atr_value: float,
        rr_multiple: float,
        atr_sl_multiple: float,
        created_at: datetime,
        symbol: str,
    ) -> SetupCandidate | None:
        if trend not in {"UP", "RANGE"}:
            return None

        last_gap = self._last_gap(gaps, "BULLISH")
        last_block = self._last_block(blocks, "BULLISH")
        if last_gap is None and last_block is None:
            return None

        if last_gap is not None:
            gap = cast(Any, last_gap)
            entry = (gap.lower + gap.upper) / 2.0
            base_sl = support if support is not None else recent_low
            sl = min(base_sl, gap.lower) - atr_value * atr_sl_multiple
            evidence = [f"bullish FVG {gap.lower:.3f}-{gap.upper:.3f}"]
            if support is not None:
                evidence.append(f"support near {support:.3f}")
        elif last_block is not None:
            block = cast(Any, last_block)
            entry = block.lower
            base_sl = support if support is not None else recent_low
            sl = min(base_sl, block.lower) - atr_value * atr_sl_multiple
            evidence = [f"bullish order block {block.lower:.3f}-{block.upper:.3f}"]
            if support is not None:
                evidence.append(f"support near {support:.3f}")
        else:
            return None

        if sl >= entry:
            return None
        tp = entry + max((entry - sl) * rr_multiple, atr_value * 2.0)
        confidence = 0.6
        if last_gap is not None:
            confidence += 0.2
        if last_block is not None:
            confidence += 0.15
        if support is not None:
            confidence += 0.1
        confidence = min(confidence, 0.95)
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
        *,
        trend: str,
        gaps: list[Any],
        blocks: list[Any],
        resistance: float | None,
        recent_high: float,
        atr_value: float,
        rr_multiple: float,
        atr_sl_multiple: float,
        created_at: datetime,
        symbol: str,
    ) -> SetupCandidate | None:
        if trend not in {"DOWN", "RANGE"}:
            return None

        last_gap = self._last_gap(gaps, "BEARISH")
        last_block = self._last_block(blocks, "BEARISH")
        if last_gap is None and last_block is None:
            return None

        if last_gap is not None:
            gap = cast(Any, last_gap)
            entry = (gap.lower + gap.upper) / 2.0
            base_sl = resistance if resistance is not None else recent_high
            sl = max(base_sl, gap.upper) + atr_value * atr_sl_multiple
            evidence = [f"bearish FVG {gap.lower:.3f}-{gap.upper:.3f}"]
            if resistance is not None:
                evidence.append(f"resistance near {resistance:.3f}")
        elif last_block is not None:
            block = cast(Any, last_block)
            entry = block.upper
            base_sl = resistance if resistance is not None else recent_high
            sl = max(base_sl, block.upper) + atr_value * atr_sl_multiple
            evidence = [f"bearish order block {block.lower:.3f}-{block.upper:.3f}"]
            if resistance is not None:
                evidence.append(f"resistance near {resistance:.3f}")
        else:
            return None

        if sl <= entry:
            return None
        tp = entry - max((sl - entry) * rr_multiple, atr_value * 2.0)
        confidence = 0.6
        if last_gap is not None:
            confidence += 0.2
        if last_block is not None:
            confidence += 0.15
        if resistance is not None:
            confidence += 0.1
        confidence = min(confidence, 0.95)
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

    def _last_gap(self, gaps: list[Any], direction: str) -> Any | None:
        for gap in reversed(gaps):
            if getattr(gap, "direction", None) == direction:
                return gap
        return None

    def _last_block(self, blocks: list[Any], direction: str) -> Any | None:
        for block in reversed(blocks):
            if getattr(block, "direction", None) == direction:
                return block
        return None

    def _nearest_level(self, levels: list[float], last_price: float, kind: str) -> float | None:
        if not levels:
            return None
        if kind == "support":
            eligible = [level for level in levels if level < last_price]
            return max(eligible) if eligible else None
        eligible = [level for level in levels if level > last_price]
        return min(eligible) if eligible else None

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
            except ValueError as exc:  # pragma: no cover - defensive coercion
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
            except ValueError as exc:  # pragma: no cover - defensive coercion
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
            except ValueError as exc:  # pragma: no cover - defensive coercion
                raise ValueError(f"{field} must be between {lower} and {upper}") from exc
        else:
            raise ValueError(f"{field} must be between {lower} and {upper}")
        if not lower <= number <= upper:
            raise ValueError(f"{field} must be between {lower} and {upper}")
        return number
