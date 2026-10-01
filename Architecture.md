# Architecture — JARVIS

## 1. Principles
1. **Deterministic first.** Indicators, structure, SL/TP math, R:R, scoring = pure Python. LLM only for news interpretation and the human-readable rationale, with strict structured output (Pydantic).
2. **Read-only.** No `order_send`, `order_check`, or trade functions anywhere. A test greps for them.
3. **Typed contracts.** Every node reads/writes Pydantic models in the shared LangGraph state.
4. **Config-driven.** Instruments, strategies, weights, thresholds live in YAML.
5. **Cache everything.** Candles and news cached; agents never re-fetch within a cycle.

## 2. Stack
Python 3.11+, uv, LangGraph, langchain-anthropic (Claude: Haiku for news, Sonnet for Jarvis rationale), Pydantic v2, MetaTrader5, pandas/numpy, pandas-ta (or `ta`), timesfm + torch (CPU ok), feedparser + httpx (news), SQLite via SQLModel, APScheduler, FastAPI + SSE, React + Vite + TypeScript + Tailwind (dashboard), pytest, ruff, mypy.

> Verify every package/version exists before installing (see Rules.md).

## 3. Graph flow (LangGraph)
```
START
 └─► Vision (fetch+validate candles for all symbols)
      └─► Nick Fury (global news/macro, once per cycle)
           └─► fan-out per instrument (Send API / parallel subgraphs)
                ┌──────────────── Instrument subgraph ────────────────┐
                │ Instrument Agent (Iron Man/Cap/Thor/Hulk/B.Panther)│
                │   ├─► Doctor Strange (structure, MTF)               │
                │   ├─► Quicksilver (TimesFM forecast)                │
                │   └─► Strategy agents in parallel                   │
                │        Hawkeye · Black Widow · Falcon · Ant-Man · Wasp
                │   └─► Instrument Agent merges → candidate setups    │
                │   └─► War Machine (risk validation per candidate)   │
                └─────────────────────────────────────────────────────┘
           └─► Jarvis (supervisor: confluence scoring → decision per instrument)
                └─► Coulson (persist signal, track outcomes)
                     └─► API/SSE → Dashboard
END
```
Triggers: scheduler per cycle (default every 15 min, on M15 candle close) + manual "run now" from dashboard.

## 4. Folder structure
```
jarvis/
├── CLAUDE.md                  # short pointer to docs (≤30 lines)
├── PRD.md Architecture.md Rules.md Design.md Task.md Memory.md
├── pyproject.toml  .env.example  .gitignore
├── config/
│   ├── instruments.yaml       # symbol map, sessions, ATR mult, agent name
│   ├── strategies.yaml        # enabled, weights, params
│   └── jarvis.yaml            # thresholds, risk %, cycle interval
├── src/jarvis/
│   ├── schemas/               # Pydantic models (single source of truth)
│   ├── data/                  # provider.py (interface), mt5_provider.py, mock_provider.py, cache.py
│   ├── indicators/            # atr, ema, swings, fvg, order_blocks, fib, zones
│   ├── agents/
│   │   ├── vision.py  strange.py  fury.py  quicksilver.py
│   │   ├── war_machine.py  coulson.py  jarvis.py
│   │   ├── instruments/       # base.py + profiles; one class per hero
│   │   └── strategies/        # base.py, hawkeye.py, black_widow.py, falcon.py, ant_man.py, wasp.py
│   ├── graph/                 # state.py, instrument_graph.py, main_graph.py
│   ├── services/              # scheduler.py, signal_store.py, outcome_tracker.py, alerts.py
│   ├── api/                   # main.py (FastAPI), routes, sse.py
│   └── utils/                 # logging.py, time.py, errors.py
├── web/                       # React dashboard (see Design.md)
└── tests/                     # unit/, integration/, fixtures/ (recorded candles)
```

## 5. Core schemas (Pydantic, `schemas/`)
```python
Direction = Literal["BUY","SELL"]
Decision  = Literal["TRADE","NO_TRADE"]

class MarketStructure(BaseModel):
    symbol: str; timeframe_trends: dict[str, Literal["UP","DOWN","RANGE"]]
    last_bos: dict | None; last_choch: dict | None
    key_levels: list[float]; atr: dict[str,float]
    volatility_regime: Literal["LOW","NORMAL","HIGH"]; session: str

class NewsImpact(BaseModel):
    symbol: str; bias: Literal["BULLISH","BEARISH","NEUTRAL"]
    impact: int  # 0-10
    blackout_until: datetime | None; events: list[dict]; summary: str

class Forecast(BaseModel):
    symbol: str; horizon_bars: int; timeframe: str
    median: list[float]; q10: list[float]; q90: list[float]
    expected_direction: Literal["UP","DOWN","FLAT"]; strength: float  # 0-1

class SetupCandidate(BaseModel):
    symbol: str; strategy: str; agent: str; direction: Direction
    entry: float; sl: float; tp: float; confidence: float  # 0-1
    evidence: list[str]; created_at: datetime

class RiskAssessment(BaseModel):
    candidate_id: str; valid: bool; rr: float; sl_atr_mult: float
    spread_ok: bool; suggested_lot: float | None; issues: list[str]

class Signal(BaseModel):
    id: str; symbol: str; decision: Decision; direction: Direction | None
    entry: float | None; sl: float | None; tp: float | None; rr: float | None
    confidence: float; score_breakdown: dict[str,float]
    agent_verdicts: dict[str,str]; rationale: str
    status: Literal["OPEN","TP_HIT","SL_HIT","EXPIRED","SKIPPED"]
    created_at: datetime; expires_at: datetime
```
LangGraph state: `JarvisState` with `cycle_id, candles_ref, news, per_symbol: dict[str, SymbolState], signals: list[Signal], errors: list[AgentError]` using reducers for parallel merges.

## 6. Jarvis decision logic (`config/jarvis.yaml`)
```
score = Σ(w_strategy·confidence for aligned strategies)
      + w_structure·alignment + w_forecast·forecast_agreement + w_news·news_alignment
TRADE only if:
  score ≥ min_score  AND  ≥2 strategies agree on direction
  AND War Machine valid (RR ≥ 1.5, SL within ATR bounds, spread ok)
  AND no news blackout  AND forecast not strongly opposite
  AND no existing OPEN signal for symbol/direction
Entry/SL/TP = highest-confidence valid candidate among aligned ones (not averaged blindly).
```
The LLM writes `rationale` from the structured evidence only; it cannot change numbers.

## 7. Data layer
- `DataProvider` interface: `get_candles(symbol, tf, n)`, `get_symbol_info`, `get_tick`.
- `MT5Provider` uses the `MetaTrader5` package (**Windows-native**). On macOS/Linux: run MT5 under Wine with an RPyC bridge (e.g., mt5linux) — verify before adopting. `MockProvider` replays recorded CSV/parquet for tests and development without MT5.
- Allowed MT5 calls: `initialize, copy_rates_from_pos, symbol_info, symbol_info_tick, shutdown`. Anything else is forbidden.
- Cache: parquet per symbol/timeframe; refresh only on new bar.

## 8. TimesFM (Quicksilver)
Load once (singleton). Input: last 512 closes per symbol (M15/H1). Output: 32–64 bar quantile forecast. Convert to `Forecast` (direction, strength = |median drift| / ATR, clipped). Forecast is a **supporting input only**, never a standalone trigger. Verify the current `timesfm` package API from the official google-research/timesfm repo before coding.

## 9. News (Nick Fury)
Sources (free first): economic calendar feed, RSS (Reuters/FXStreet/Kitco/CoinDesk etc. — verify URLs live), optional Finnhub/NewsAPI key. Pipeline: fetch → dedupe → keyword/instrument filter → Haiku classifies impact (JSON schema) → per-symbol `NewsImpact`. High-impact events (FOMC, CPI, NFP, EIA) create blackout windows (config minutes before/after).

## 10. Persistence & API
SQLite tables: `signals`, `cycles`, `agent_runs`, `news_items`, `outcomes`. FastAPI: `GET /signals`, `GET /signals/{id}`, `GET /agents/status`, `GET /news`, `GET /stats`, `POST /run`, `GET /stream` (SSE). Dashboard consumes only these.

## 11. Error handling flow
Agent failure → caught in node wrapper → `AgentError` appended to state → graph continues with degraded input → Jarvis lowers confidence or returns NO_TRADE with reason `DEGRADED:<agent>`. Never fabricate data.

## 12. Code conventions
Type hints everywhere; `ruff` + `mypy --strict` on `schemas/` and `agents/`; functions ≤ 40 lines; docstring one-liner per public function; snake_case modules, PascalCase classes; logging via `structlog`/stdlib JSON, no `print`; secrets only via `.env`; timestamps UTC ISO-8601; prices as float with symbol digits from `symbol_info`.
