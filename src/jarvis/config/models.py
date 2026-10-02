from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ConfigModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class InstrumentConfig(ConfigModel):
    symbol: str
    broker_symbol: str
    agent: str
    sessions: list[str]
    atr_multipliers: dict[str, float]


class InstrumentsConfig(ConfigModel):
    instruments: list[InstrumentConfig] = Field(min_length=1)


class StrategyConfig(ConfigModel):
    name: str
    enabled: bool
    weight: float = Field(gt=0)
    params: dict[str, Any]


class StrategiesConfig(ConfigModel):
    strategies: list[StrategyConfig] = Field(min_length=1)


class JarvisConfig(ConfigModel):
    min_score: float = Field(ge=0)
    minimum_rr: float = Field(gt=0)
    min_agreeing_strategies: int = Field(ge=1)
    risk_percent: float = Field(gt=0, le=100)
    cycle_interval_seconds: int = Field(gt=0)
