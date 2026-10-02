"""Tests for Instrument base profiles (T4.1)."""

from jarvis.agents.instruments.base import BaseInstrumentAgent
from jarvis.agents.instruments.black_panther import BlackPanther
from jarvis.agents.instruments.captain_america import CaptainAmerica
from jarvis.agents.instruments.hulk import Hulk
from jarvis.agents.instruments.iron_man import IronMan
from jarvis.agents.instruments.thor import Thor
from jarvis.config.models import InstrumentConfig


def _config(agent_name: str, symbol: str) -> InstrumentConfig:
    return InstrumentConfig(
        symbol=symbol,
        broker_symbol=symbol,
        agent=agent_name,
        sessions=[],
        atr_multipliers={"hawkeye": 2.0},
    )


def test_base_instrument_properties() -> None:
    cfg = _config("iron_man", "XAUUSD")
    agent = IronMan(cfg)
    assert agent.name == "iron_man"
    assert agent.symbol == "XAUUSD"
    assert agent.broker_symbol == "XAUUSD"
    assert agent.is_market_open() is True
    assert agent._get_atr_multiplier("hawkeye") == 2.0
    assert agent._get_atr_multiplier("missing", 1.5) == 1.5


def test_crypto_profiles_always_open() -> None:
    thor = Thor(_config("thor", "BTCUSD"))
    hulk = Hulk(_config("hulk", "ETHUSD"))
    
    assert thor.is_market_open() is True
    assert hulk.is_market_open() is True


def test_other_profiles_exist() -> None:
    cap = CaptainAmerica(_config("captain_america", "XAGUSD"))
    panther = BlackPanther(_config("black_panther", "USOUSD"))
    
    assert isinstance(cap, BaseInstrumentAgent)
    assert isinstance(panther, BaseInstrumentAgent)
