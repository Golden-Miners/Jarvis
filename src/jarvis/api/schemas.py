"""API response schemas matching API_Integrations.md §7."""
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

Decision = Literal["TRADE", "NO_TRADE"]
Direction = Literal["BUY", "SELL"]
SignalStatus = Literal["OPEN", "TP_HIT", "SL_HIT", "EXPIRED", "SKIPPED"]
Bias = Literal["BULLISH", "BEARISH", "NEUTRAL"]
ForecastDirection = Literal["UP", "DOWN", "FLAT"]
VolatilityRegime = Literal["LOW", "NORMAL", "HIGH"]
AgentStatusEnum = Literal["OK", "DEGRADED", "ERROR", "SKIPPED"]
CycleStatus = Literal["RUNNING", "COMPLETED", "DEGRADED", "FAILED"]
CycleTrigger = Literal["SCHEDULED", "MANUAL"]
EventImportance = Literal["LOW", "MEDIUM", "HIGH"]


class ErrorResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    error: dict[str, str] = Field(..., description="Error code, message, request_id")


class SignalResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    symbol: str
    decision: Decision
    direction: Direction | None
    entry: float | None
    sl: float | None
    tp: float | None
    rr: float | None
    confidence: float = Field(..., ge=0.0, le=1.0)
    score: float
    score_breakdown: dict[str, float]
    agent_verdicts: dict[str, str]
    rationale: str
    status: SignalStatus
    created_at: str
    expires_at: str
    no_trade_reason: str | None = None


class SignalListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    data: list[SignalResponse]
    next_cursor: str | None = None


class SignalDetailResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    signal: SignalResponse
    verdicts: list[dict[str, Any]] = Field(default_factory=list)
    candidate: dict[str, Any] | None = None
    risk: dict[str, Any] | None = None


class InstrumentResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    symbol: str
    broker_symbol: str
    agent_name: str
    digits: int | None = None
    point: float | None = None
    enabled: bool
    latest_decision: Decision | None = None
    latest_direction: Direction | None = None
    latest_confidence: float | None = None
    latest_status: SignalStatus | None = None


class AgentStatusResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    agent: str
    symbol: str | None
    last_run: str
    latency_ms: int
    status: AgentStatusEnum
    error: str | None = None


class NewsImpactResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    source: str
    url: str
    symbol: str
    bias: Bias
    impact: int
    blackout_until: str | None
    published_at: str
    summary: str


class NewsListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    data: list[NewsImpactResponse]
    next_cursor: str | None = None


class CalendarEventResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    name: str
    currency: str
    importance: EventImportance
    event_time: str
    blackout_start: str | None = None
    blackout_end: str | None = None


class CalendarListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    data: list[CalendarEventResponse]
    next_cursor: str | None = None


class StatsByStrategy(BaseModel):
    model_config = ConfigDict(extra="forbid")
    win_rate: float
    avg_rr: float
    count: int


class StatsByInstrument(BaseModel):
    model_config = ConfigDict(extra="forbid")
    win_rate: float
    avg_rr: float
    count: int


class StatsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    total_signals: int
    win_rate: float
    avg_rr: float
    expectancy: float
    by_strategy: dict[str, StatsByStrategy]
    by_instrument: dict[str, StatsByInstrument]


class CycleRunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    trigger: CycleTrigger = "MANUAL"


class CycleRunResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    cycle_id: str
    status: CycleStatus
    message: str


class InstrumentConfigUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    enabled: bool


class HealthResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: Literal["healthy", "degraded", "unhealthy"]
    adapters: dict[str, Literal["healthy", "degraded", "unhealthy", "unknown"]]


class SSEEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: str
    data: dict[str, Any]
    timestamp: str


# SSE event types per spec
SSE_EVENT_TYPES = Literal["signal.created", "signal.updated", "cycle.status", "agent.health"]