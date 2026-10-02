from jarvis.agents.instruments.base import BaseInstrumentAgent


class Hulk(BaseInstrumentAgent):
    """Hulk profile for Ethereum (ETHUSD). Features 24/7 market awareness."""

    def is_market_open(self) -> bool:
        """Crypto is always open 24/7."""
        return True
