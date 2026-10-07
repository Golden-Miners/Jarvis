"""SQLModel tables mirroring Backend_Schema.md (T6.1 subset).

Tables: instruments, cycles, config_snapshots, signals, signal_verdicts,
outcomes, agent_runs, market_structure, key_levels, forecasts,
news_items, news_impacts, calendar_events, setup_candidates,
risk_assessments, users, audit_log. Datetimes are stored as ISO-8601 UTC TEXT per Backend_Schema §2.
"""
# mypy: ignore-errors
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import CheckConstraint, Column, Index, Text
from sqlalchemy import text as sa_text
from sqlalchemy.types import TypeDecorator
from sqlmodel import Field, SQLModel


class UTCText(TypeDecorator[str]):
    """Store datetimes as ISO-8601 UTC TEXT."""

    impl = Text
    cache_ok = True

    def process_bind_param(self, value: Any, dialect: Any) -> str | None:
        if value is None:
            return None
        return value.astimezone(UTC).isoformat()

    def process_result_value(self, value: Any, dialect: Any) -> str | None:
        if value is None:
            return None
        parsed = datetime.fromisoformat(str(value))
        if parsed.tzinfo is None:  # type: ignore
            parsed = parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC)


class InstrumentModel(SQLModel, table=True):
    """Canonical instrument metadata (FK target for signals.symbol)."""

    __tablename__ = "instruments"

    symbol: str = Field(primary_key=True)
    broker_symbol: str
    agent_name: str
    digits: int | None = None
    point: float | None = None
    enabled: int = Field(default=1)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), sa_column=Column(UTCText, nullable=False)
    )
    __table_args__ = (CheckConstraint("enabled IN (0,1)"),)


class CycleModel(SQLModel, table=True):
    """One graph cycle (P0 bookkeeping for signals and agent runs)."""

    __tablename__ = "cycles"

    id: str = Field(primary_key=True)
    trigger: str
    status: str
    config_hash: str
    started_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), sa_column=Column(UTCText, nullable=False)
    )
    finished_at: datetime | None = Field(default=None, sa_column=Column(UTCText))
    duration_ms: int | None = None
    __table_args__ = (
        CheckConstraint("trigger IN ('SCHEDULED','MANUAL')"),
        CheckConstraint("status IN ('RUNNING','COMPLETED','DEGRADED','FAILED')"),
    )


class ConfigSnapshotModel(SQLModel, table=True):
    """Reproducible config snapshot linked to cycles via hash."""

    __tablename__ = "config_snapshots"

    hash: str = Field(primary_key=True)
    yaml_text: str
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), sa_column=Column(UTCText, nullable=False)
    )


class SignalModel(SQLModel, table=True):
    """Persisted trade signal (mirrors schemas.Signal + DB-only columns)."""

    __tablename__ = "signals"

    id: str = Field(primary_key=True)
    cycle_id: str = Field(foreign_key="cycles.id", index=True)
    symbol: str = Field(foreign_key="instruments.symbol", index=True)
    decision: str
    direction: str | None = None
    entry: float | None = None
    sl: float | None = None
    tp: float | None = None
    rr: float | None = None
    confidence: float
    score: float
    no_trade_reason: str | None = None
    rationale: str
    source_candidate_id: str | None = None
    status: str
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), sa_column=Column(UTCText, nullable=False)
    )
    expires_at: datetime | None = Field(default=None, sa_column=Column(UTCText))
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), sa_column=Column(UTCText, nullable=False)
    )
    __table_args__ = (
        CheckConstraint("decision IN ('TRADE','NO_TRADE')"),
        CheckConstraint("direction IS NULL OR direction IN ('BUY','SELL')"),
        CheckConstraint("status IN ('OPEN','TP_HIT','SL_HIT','EXPIRED','SKIPPED')"),
        CheckConstraint(
            "decision='NO_TRADE' OR "
            "(direction IS NOT NULL AND entry IS NOT NULL AND sl IS NOT NULL AND tp IS NOT NULL)"
        ),
        CheckConstraint("decision='TRADE' OR no_trade_reason IS NOT NULL"),
        CheckConstraint(
            "direction IS NULL OR "
            "(direction='BUY' AND sl<entry AND tp>entry) OR "
            "(direction='SELL' AND sl>entry AND tp<entry)"
        ),
        CheckConstraint("confidence BETWEEN 0 AND 1"),
        Index("ix_signals_symbol_created", "symbol", "created_at"),
        Index("ix_signals_status", "status"),
        Index(
            "ux_open_signal", "symbol", "direction",
            unique=True, sqlite_where=sa_text("status = 'OPEN'")
        ),
    )


class SignalVerdictModel(SQLModel, table=True):
    """Per-agent evidence row for a signal (populated once verdicts are structured)."""

    __tablename__ = "signal_verdicts"

    id: str = Field(primary_key=True)
    signal_id: str = Field(foreign_key="signals.id", index=True)
    agent: str
    verdict: str
    weight: float
    contribution: float
    note: str | None = None
    __table_args__ = (
        CheckConstraint("verdict IN ('BUY','SELL','NEUTRAL','VETO','ERROR')"),
    )


class OutcomeModel(SQLModel, table=True):
    """Hypothetical outcome of a signal (Coulson). One per signal."""

    __tablename__ = "outcomes"

    signal_id: str = Field(primary_key=True, foreign_key="signals.id")
    result: str
    resolved_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), sa_column=Column(UTCText, nullable=False)
    )
    r_multiple: float
    max_favorable: float | None = None
    max_adverse: float | None = None
    __table_args__ = (CheckConstraint("result IN ('TP_HIT','SL_HIT','EXPIRED')"),)


class AgentRunModel(SQLModel, table=True):
    """Agent run record per cycle."""

    __tablename__ = "agent_runs"

    id: str = Field(primary_key=True)
    cycle_id: str = Field(foreign_key="cycles.id", index=True)
    agent: str
    symbol: str | None = Field(default=None, foreign_key="instruments.symbol")
    status: str
    error_code: str | None = None
    error_message: str | None = None
    latency_ms: int | None = None
    llm_tokens_in: int | None = None
    llm_tokens_out: int | None = None
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), sa_column=Column(UTCText, nullable=False)
    )
    __table_args__ = (
        CheckConstraint("status IN ('OK','DEGRADED','ERROR','SKIPPED')"),
        Index("ix_agent_runs_cycle", "cycle_id"),
    )


class MarketStructureModel(SQLModel, table=True):
    """Market structure snapshot per symbol per cycle."""

    __tablename__ = "market_structure"

    id: str = Field(primary_key=True)
    cycle_id: str = Field(foreign_key="cycles.id", index=True)
    symbol: str = Field(foreign_key="instruments.symbol", index=True)
    trend_m15: str | None = None
    trend_h1: str | None = None
    trend_h4: str | None = None
    trend_d1: str | None = None
    atr_m15: float | None = None
    atr_h1: float | None = None
    volatility_regime: str | None = None
    session: str
    last_bos_direction: str | None = None
    last_choch_direction: str | None = None
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), sa_column=Column(UTCText, nullable=False)
    )
    __table_args__ = (
        CheckConstraint("volatility_regime IN ('LOW','NORMAL','HIGH')"),
    )


class KeyLevelModel(SQLModel, table=True):
    """Key price level from market structure."""

    __tablename__ = "key_levels"

    id: str = Field(primary_key=True)
    structure_id: str = Field(foreign_key="market_structure.id", index=True)
    price: float
    kind: str
    __table_args__ = (
        CheckConstraint("kind IN ('SUPPORT','RESISTANCE','SUPPLY','DEMAND','LIQUIDITY')"),
    )


class ForecastModel(SQLModel, table=True):
    """TimesFM forecast per symbol/timeframe per cycle."""

    __tablename__ = "forecasts"

    id: str = Field(primary_key=True)
    cycle_id: str = Field(foreign_key="cycles.id", index=True)
    symbol: str = Field(foreign_key="instruments.symbol", index=True)
    timeframe: str
    horizon_bars: int
    expected_direction: str
    strength: float
    median_end: float
    q10_end: float
    q90_end: float
    model_version: str
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), sa_column=Column(UTCText, nullable=False)
    )
    __table_args__ = (
        CheckConstraint("expected_direction IN ('UP','DOWN','FLAT')"),
        CheckConstraint("strength BETWEEN 0 AND 1"),
    )


class NewsItemModel(SQLModel, table=True):
    """Raw news item from feeds."""

    __tablename__ = "news_items"

    id: str = Field(primary_key=True)
    source: str
    url: str
    url_hash: str
    title: str
    published_at: datetime = Field(sa_column=Column(UTCText, nullable=False))
    fetched_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), sa_column=Column(UTCText, nullable=False)
    )
    raw: str | None = None
    __table_args__ = (
        Index("ux_news_items_url_hash", "url_hash", unique=True),
    )


class NewsImpactModel(SQLModel, table=True):
    """Classified news impact per symbol per cycle."""

    __tablename__ = "news_impacts"

    id: str = Field(primary_key=True)
    news_item_id: str = Field(foreign_key="news_items.id", index=True)
    cycle_id: str = Field(foreign_key="cycles.id", index=True)
    symbol: str = Field(foreign_key="instruments.symbol", index=True)
    bias: str
    impact: int
    summary: str
    model: str
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), sa_column=Column(UTCText, nullable=False)
    )
    __table_args__ = (
        CheckConstraint("bias IN ('BULLISH','BEARISH','NEUTRAL')"),
        CheckConstraint("impact BETWEEN 0 AND 10"),
    )


class CalendarEventModel(SQLModel, table=True):
    """Economic calendar event with blackout windows."""

    __tablename__ = "calendar_events"

    id: str = Field(primary_key=True)
    name: str
    currency: str
    importance: str
    event_time: datetime = Field(sa_column=Column(UTCText, nullable=False))
    blackout_start: datetime | None = Field(default=None, sa_column=Column(UTCText))
    blackout_end: datetime | None = Field(default=None, sa_column=Column(UTCText))
    __table_args__ = (
        CheckConstraint("importance IN ('LOW','MEDIUM','HIGH')"),
        Index("ux_calendar_name_time", "name", "event_time", unique=True),
    )


class SetupCandidateModel(SQLModel, table=True):
    """Strategy setup candidate before risk assessment."""

    __tablename__ = "setup_candidates"

    id: str = Field(primary_key=True)
    cycle_id: str = Field(foreign_key="cycles.id", index=True)
    symbol: str = Field(foreign_key="instruments.symbol", index=True)
    strategy: str
    agent: str
    direction: str
    entry: float
    sl: float
    tp: float
    confidence: float
    evidence: str  # JSON list[str]
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), sa_column=Column(UTCText, nullable=False)
    )
    __table_args__ = (
        CheckConstraint("direction IN ('BUY','SELL')"),
        CheckConstraint("confidence BETWEEN 0 AND 1"),
        Index("ix_candidates_cycle_symbol", "cycle_id", "symbol"),
    )


class RiskAssessmentModel(SQLModel, table=True):
    """Risk assessment for a setup candidate."""

    __tablename__ = "risk_assessments"

    id: str = Field(primary_key=True)
    candidate_id: str = Field(foreign_key="setup_candidates.id", unique=True)
    valid: int
    rr: float
    sl_atr_mult: float
    spread_ok: int
    suggested_lot: float | None = None
    issues: str = Field(default="[]")  # JSON list[str]
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), sa_column=Column(UTCText, nullable=False)
    )
    __table_args__ = (
        CheckConstraint("valid IN (0,1)"),
        CheckConstraint("spread_ok IN (0,1)"),
    )


class UserModel(SQLModel, table=True):
    """System user (for audit trail)."""

    __tablename__ = "users"

    id: str = Field(primary_key=True)
    username: str = Field(unique=True)
    password_hash: str
    role: str
    active: int = Field(default=1)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), sa_column=Column(UTCText, nullable=False)
    )
    __table_args__ = (
        CheckConstraint("role IN ('OWNER','VIEWER')"),
        CheckConstraint("active IN (0,1)"),
    )


class AuditLogModel(SQLModel, table=True):
    """Append-only audit log."""

    __tablename__ = "audit_log"

    id: str = Field(primary_key=True)
    ts: datetime = Field(sa_column=Column(UTCText, nullable=False))
    actor: str
    action: str
    entity: str | None = None
    entity_id: str | None = None
    payload: str | None = None