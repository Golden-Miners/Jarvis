from datetime import time
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


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


class SessionWindow(ConfigModel):
    name: str = Field(min_length=1)
    start_utc: time
    end_utc: time


class DoctorStrangeSettings(ConfigModel):
    primary_timeframe: str = Field(min_length=1)
    ema_period: int = Field(gt=0)
    atr_period: int = Field(gt=0)
    volatility_window: int = Field(gt=0)
    low_volatility_percentile: float = Field(ge=0, le=1)
    high_volatility_percentile: float = Field(ge=0, le=1)
    swing_left: int = Field(gt=0)
    swing_right: int = Field(gt=0)
    zone_tolerance: float = Field(ge=0)

    @model_validator(mode="after")
    def validate_volatility_percentiles(self) -> "DoctorStrangeSettings":
        if self.low_volatility_percentile >= self.high_volatility_percentile:
            raise ValueError("low volatility percentile must be below high percentile")
        return self
