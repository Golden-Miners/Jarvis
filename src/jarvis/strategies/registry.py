from collections.abc import Callable

from jarvis.config.models import StrategiesConfig
from jarvis.strategies.base import BaseStrategy

StrategyFactory = Callable[[dict[str, object]], BaseStrategy]


class StrategyRegistry:
    def __init__(self) -> None:
        self._factories: dict[str, StrategyFactory] = {}

    def register(self, name: str, factory: StrategyFactory) -> None:
        if not name:
            raise ValueError("strategy name must not be empty")
        if name in self._factories:
            raise ValueError(f"strategy already registered: {name}")
        self._factories[name] = factory

    def create_enabled(self, config: StrategiesConfig) -> dict[str, BaseStrategy]:
        instances: dict[str, BaseStrategy] = {}
        configured_names: set[str] = set()
        for strategy_config in config.strategies:
            name = strategy_config.name
            if name in configured_names:
                raise ValueError(f"strategy configured more than once: {name}")
            configured_names.add(name)
            if not strategy_config.enabled:
                continue
            try:
                factory = self._factories[name]
            except KeyError as error:
                message = f"no strategy registered for configured strategy: {name}"
                raise ValueError(message) from error
            instance = factory(dict(strategy_config.params))
            if instance.name != name:
                message = (
                    f"registered strategy name mismatch: configured {name}, "
                    f"instance {instance.name}"
                )
                raise ValueError(
                    message
                )
            instances[name] = instance
        return instances
