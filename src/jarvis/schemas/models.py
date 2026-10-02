from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

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
