from jarvis.agents.instruments.base import BaseInstrumentAgent


class Thor(BaseInstrumentAgent):
    """Thor profile for Bitcoin (BTCUSD). Features 24/7 market awareness."""

    def is_market_open(self) -> bool:
        """Crypto is always open 24/7."""
        return True
