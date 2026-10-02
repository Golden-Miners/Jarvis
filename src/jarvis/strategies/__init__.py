from jarvis.strategies.ant_man import AntMan
from jarvis.strategies.base import BaseStrategy
from jarvis.strategies.black_widow import BlackWidow
from jarvis.strategies.context import StrategyContext
from jarvis.strategies.falcon import Falcon
from jarvis.strategies.hawkeye import Hawkeye
from jarvis.strategies.registry import StrategyRegistry
from jarvis.strategies.wasp import Wasp

__all__ = [
    "AntMan",
    "BaseStrategy",
    "BlackWidow",
    "Falcon",
    "Hawkeye",
    "StrategyContext",
    "StrategyRegistry",
    "Wasp",
]


def default_strategy_registry() -> StrategyRegistry:
    registry = StrategyRegistry()
    registry.register("hawkeye", lambda params: Hawkeye(params))
    registry.register("black_widow", lambda params: BlackWidow(params))
    registry.register("falcon", lambda params: Falcon(params))
    registry.register("ant_man", lambda params: AntMan(params))
    registry.register("wasp", lambda params: Wasp(params))
    return registry
