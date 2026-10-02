from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

Direction = Literal["BUY", "SELL"]
Decision = Literal["TRADE", "NO_TRADE"]
Trend = Literal["UP", "DOWN", "RANGE"]
Bias = Literal["BULLISH", "BEARISH", "NEUTRAL"]
VolatilityRegime = Literal["LOW", "NORMAL", "HIGH"]
ForecastDirection = Literal["UP", "DOWN", "FLAT"]
SignalStatus = Literal["OPEN", "TP_HIT", "SL_HIT", "EXPIRED", "SKIPPED"]


class MarketStructure(BaseModel):
    symbol: str
    timeframe_trends: dict[str, Trend]
    last_bos: dict[str, Any] | None = None
    last_choch: dict[str, Any] | None = None
    key_levels: list[float]
    atr: dict[str, float]
    volatility_regime: VolatilityRegime
    session: str


class NewsImpact(BaseModel):
    symbol: str
    bias: Bias
    impact: int = Field(ge=0, le=10)
    blackout_until: datetime | None = None
    events: list[dict[str, Any]] = Field(default_factory=list)
    summary: str = ""


class Forecast(BaseModel):
    symbol: str
    horizon_bars: int = Field(gt=0)
    timeframe: str
    median: list[float]
    q10: list[float]
    q90: list[float]
    expected_direction: ForecastDirection
    strength: float = Field(ge=0.0, le=1.0)


class SetupCandidate(BaseModel):
    symbol: str
    strategy: str
    agent: str
    direction: Direction
    entry: float
    sl: float
    tp: float
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: list[str]
    created_at: datetime


class RiskAssessment(BaseModel):
    candidate_id: str
    valid: bool
    rr: float
    sl_atr_mult: float
    spread_ok: bool
    suggested_lot: float | None = None
    issues: list[str]


class Signal(BaseModel):
    id: str
    symbol: str
    decision: Decision
    direction: Direction | None = None
    entry: float | None = None
    sl: float | None = None
    tp: float | None = None
    rr: float | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    score_breakdown: dict[str, float]
    agent_verdicts: dict[str, str]
    rationale: str
    status: SignalStatus
    created_at: datetime
    expires_at: datetime


class Candle(BaseModel):
    timestamp: datetime
    open: float = Field(gt=0)
    high: float = Field(gt=0)
    low: float = Field(gt=0)
    close: float = Field(gt=0)
    volume: float = Field(ge=0)

    @field_validator("timestamp")
    @classmethod
    def timestamp_is_utc(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("timestamp must include a timezone")
        return value.astimezone(UTC)

    @model_validator(mode="after")
    def validate_ohlc(self) -> "Candle":
        if self.high < max(self.open, self.close, self.low):
            raise ValueError("high must be at least open, close, and low")
        if self.low > min(self.open, self.close, self.high):
            raise ValueError("low must be at most open, close, and high")
        return self


class SymbolInfo(BaseModel):
    symbol: str
    digits: int = Field(ge=0)
    point: float = Field(gt=0)
    trade_tick_size: float = Field(gt=0)
    trade_tick_value: float = Field(ge=0)
    volume_min: float = Field(gt=0)
    volume_max: float = Field(gt=0)
    volume_step: float = Field(gt=0)

    @model_validator(mode="after")
    def validate_volume_range(self) -> "SymbolInfo":
        if self.volume_max < self.volume_min:
            raise ValueError("volume_max must be at least volume_min")
        return self


class Tick(BaseModel):
    timestamp: datetime
    bid: float = Field(gt=0)
    ask: float = Field(gt=0)

    @field_validator("timestamp")
    @classmethod
    def timestamp_is_utc(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("timestamp must include a timezone")
        return value.astimezone(UTC)

    @model_validator(mode="after")
    def validate_spread(self) -> "Tick":
        if self.ask < self.bid:
            raise ValueError("ask must be at least bid")
        return self


class InstrumentMarketData(BaseModel):
    symbol: str
    candles: dict[str, list[Candle]]
    symbol_info: SymbolInfo
    tick: Tick


class VisionResult(BaseModel):
    instruments: dict[str, InstrumentMarketData]
