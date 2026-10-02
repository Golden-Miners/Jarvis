from __future__ import annotations

from jarvis.config.models import InstrumentConfig


class BaseInstrumentAgent:
    """Base class for instrument-specific logic and profiles."""

    def __init__(self, config: InstrumentConfig) -> None:
        self.config = config

    @property
    def name(self) -> str:
        return self.config.agent

    @property
    def symbol(self) -> str:
        return self.config.symbol

    @property
    def broker_symbol(self) -> str:
        return self.config.broker_symbol

    def is_market_open(self) -> bool:
        """Return True if the market is currently open for this instrument."""
        # By default, always true. Subclasses may override based on sessions.
        return True

    def _get_atr_multiplier(self, strategy_name: str, default: float = 1.0) -> float:
        """Get the strategy-specific ATR multiplier for stop loss sizing."""
        return self.config.atr_multipliers.get(strategy_name, default)
