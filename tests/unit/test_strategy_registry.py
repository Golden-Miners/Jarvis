from datetime import UTC, datetime

import pytest

from jarvis.config.models import StrategiesConfig
from jarvis.schemas import MarketStructure, SetupCandidate
from jarvis.strategies import BaseStrategy, StrategyContext, StrategyRegistry


class FakeStrategy(BaseStrategy):
    def __init__(self, name: str, params: dict[str, object]) -> None:
        super().__init__(params)
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    def analyse(self, ctx: StrategyContext) -> list[SetupCandidate]:
        return []


def _config(*strategies: dict[str, object]) -> StrategiesConfig:
    return StrategiesConfig(strategies=strategies)


def _strategy(
    name: str,
    enabled: bool = True,
    params: dict[str, object] | None = None,
) -> dict[str, object]:
    return {
        "name": name,
        "enabled": enabled,
        "weight": 1.0,
        "params": params or {},
    }


def _context() -> StrategyContext:
    return StrategyContext(
        symbol="XAUUSD",
        candles={},
        market_structure=MarketStructure(
            symbol="XAUUSD",
            timeframe_trends={},
            key_levels=[],
            atr={},
            volatility_regime="NORMAL",
            session="UNKNOWN",
        ),
        now=datetime(2026, 1, 1, tzinfo=UTC),
    )


def test_registry_creates_enabled_strategy_and_passes_params() -> None:
    registry = StrategyRegistry()
    registry.register("hawkeye", lambda params: FakeStrategy("hawkeye", params))

    strategies = registry.create_enabled(
        _config(_strategy("hawkeye", params={"lookback": 20}))
    )

    assert strategies["hawkeye"].params == {"lookback": 20}
    assert strategies["hawkeye"].analyse(_context()) == []


def test_registry_skips_disabled_strategy_without_requiring_factory() -> None:
    registry = StrategyRegistry()

    assert registry.create_enabled(_config(_strategy("hawkeye", enabled=False))) == {}


def test_register_rejects_duplicate_name() -> None:
    registry = StrategyRegistry()

    def factory(params: dict[str, object]) -> FakeStrategy:
        return FakeStrategy("hawkeye", params)

    registry.register("hawkeye", factory)

    with pytest.raises(ValueError, match="already registered"):
        registry.register("hawkeye", factory)


def test_create_rejects_duplicate_configured_name() -> None:
    registry = StrategyRegistry()
    registry.register("hawkeye", lambda params: FakeStrategy("hawkeye", params))

    with pytest.raises(ValueError, match="configured more than once"):
        registry.create_enabled(_config(_strategy("hawkeye"), _strategy("hawkeye")))


def test_create_rejects_enabled_strategy_without_factory() -> None:
    with pytest.raises(ValueError, match="no strategy registered"):
        StrategyRegistry().create_enabled(_config(_strategy("hawkeye")))


def test_create_rejects_factory_with_mismatched_strategy_name() -> None:
    registry = StrategyRegistry()
    registry.register("hawkeye", lambda params: FakeStrategy("falcon", params))

    with pytest.raises(ValueError, match="name mismatch"):
        registry.create_enabled(_config(_strategy("hawkeye")))
