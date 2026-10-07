# Task.md — Plan & Status
Status: `TODO` · `IN_PROGRESS` · `DONE` · `BLOCKED`. Update after every task. Priority P0 > P1 > P2.

## Phase 0 — Setup & Tooling (P0)
- [x] T0.1 Init repo, uv, pyproject, folder structure, .gitignore, .env.example, ruff/mypy/pytest config — *Verify:* `uv run pytest`, Ruff, and mypy pass
- [x] T0.2 Install & verify dev resources (Context7 MCP, frontend-design skill, optional Superpowers plugin; Python libs) and log versions in Memory.md — *Verify:* `pip list`/`claude mcp list`; frontend npm tree verified. Context7 was previously Connected; two latest health checks timed out (intermittent).
- [x] T0.3 Create CLAUDE.md pointer (≤30 lines) — *Verify:* existing 5-line file links Memory.md, Task.md, Architecture.md, Design.md, PRD.md, and Rules.md

## Phase 1 — Core Contracts & Data (P0)
- [x] T1.1 Pydantic schemas + unit tests — *Verify:* pytest, Ruff, and strict mypy pass
- [x] T1.2 Config loaders (instruments/strategies/jarvis YAML) — *Verify:* pytest, Ruff, and strict mypy pass
- [x] T1.3 DataProvider interface + MockProvider + fixtures (sample fixture explicitly synthetic) — *Verify:* pytest, Ruff, strict mypy pass
- [x] T1.4 MT5Provider (read-only) + cache + data validation — *Verify:* live XAUUSD M15 fetch/cache created successfully; parquet artifact removed after verification to avoid retaining market data
- [x] T1.5 Vision agent — *Verify:* pytest, Ruff, strict mypy, and safety search pass
- [x] T1.6 No-execution safety test — *Verify:* scanner rejects forbidden APIs, permits read-only MT5 APIs, and production source audit is clean

## Phase 2 — Analysis Engine (P0)
- [x] T2.1 Indicators: ATR, EMA, swings, BOS/CHoCH, FVG, order block, zones, Fib (+tests) — *Verify:* pytest, Ruff, strict mypy, and no-execution safety tests pass
- [x] T2.2 Doctor Strange (structure/MTF/session/volatility regime) — *Verify:* pytest, Ruff, strict mypy, and no-execution safety tests pass
- [x] T2.3 War Machine (RR, ATR bounds, spread, lot suggestion) — *Verify:* pytest, Ruff, strict mypy, and no-execution safety tests pass

## Phase 3 — Strategy Agents (P0) *(parallelisable)*
- [x] T3.1 BaseStrategy + registry — *Verify:* pytest, Ruff, strict mypy, and no-execution safety tests pass
- [x] T3.2 Hawkeye (SMC/ICT) — *Verify:* pytest, Ruff, strict mypy, and no-execution safety tests pass
- [x] T3.3 Black Widow (trend-pullback) — *Verify:* pytest, Ruff, strict mypy, and no-execution safety tests pass
- [x] T3.4 Falcon (breakout) — *Verify:* pytest, Ruff, strict mypy, and no-execution safety tests pass
- [x] T3.5 Ant-Man (mean reversion) — *Verify:* pytest, Ruff, strict mypy, and no-execution safety tests pass
- [x] T3.6 Wasp (supply-demand + Fib) — *Verify:* pytest, Ruff, strict mypy, and no-execution safety tests pass

## Phase 4 — Instrument Agents & Graph (P0)
- [x] T4.1 Instrument base + 5 profiles (Iron Man, Captain America, Thor, Hulk, Black Panther)
- [x] T4.2 Instrument subgraph (Strange → strategies parallel → merge → War Machine)
- [x] T4.3 Main graph with fan-out per instrument + node error wrapper
- [x] T4.4 Jarvis supervisor scoring + rationale (LLM, schema-constrained) — *Verify:* integration test on MockProvider yields valid Signals

## Phase 5 — News & Forecast (P1)
- [x] T5.1 Nick Fury: feeds, calendar, impact classification, blackout logic — *Verify:* pytest, Ruff, strict mypy pass
- [x] T5.2 Quicksilver: TimesFM loader + forecast → `Forecast` — *Verify:* pytest, Ruff, strict mypy pass
- [x] T5.3 Wire both into graph + scoring weights — *Verify:* pytest, Ruff, strict mypy pass

## Phase 6 — Persistence, API, Scheduler (P0/P1)
- [x] T6.1 SQLite store + Coulson outcome tracker (P1) — *Verify:* 22 DB tests pass, full suite 139 passes 3× with random ordering
- [x] T6.2 FastAPI + SSE endpoints (P0) — *Verify:* API routes return Pydantic models, SSE streams signals (signal.created, signal.updated, cycle.status, agent.health)
- [x] T6.3 Scheduler on M15 close + manual run (P0) — *Verify:* APScheduler triggers cycle on M15 close; manual POST /run works

## Phase 7 — Dashboard (P0) — COMPLETED
- [x] T7.1 Scaffold web (Vite/React/TS/Tailwind) + design tokens from Design.md — *Verify:* `npm run build` passes, dev server runs, design tokens match Design.md
- [x] T7.2 Components + Signals/Agents/News views — *Verify:* SignalCard, InstrumentTile, NewsItem, AgentRow all render with glass styling
- [x] T7.3 History + Stats views, SSE live updates, responsive polish — *Verify:* Tabs with Stats/History, SSE connection, dark/light theme, responsive grid layout

## Current focus
- Phase 8 → T8.0a restore green baseline (Engineering-division build loop)

## Phase 8 — Hardening & Forward Test (P1)
*Merged with docs/audit/FIX_PLAN.md tiers 3–8 (findings F-101..F-117). Sequential; T8.4 gated by six hard pre-flight checks. Build-loop gates: full pytest green, ruff 0, mypy strict 0, no-execution AST guard + auth tests green, functional demo (backtest-lite report + mocked-LLM cycle).*

- [ ] **T8.0a Restore green baseline** — *Verify:* full pytest green, ruff 0, mypy strict 0
  - [ ] min_agreeing_strategies config 1→2 (reverses live-demo relaxation; restores test_config_loaders)
  - [ ] api/routes/cycles.py: fix build_main_graph() call (signature now takes 8 config args) → POST /cycles/run currently broken
  - [ ] api/main.py: remove duplicate SSE routes; news.py: fix nonexistent NewsImpactModel.blackout_until; signals.py/news.py datetime-vs-str; stats.py typing; utils/retry.py ParamSpec; utils/logging.py contextvars
  - [ ] Clear all ruff (73) and mypy (64) errors; raise pytest per-test timeout (cold pyarrow import >20s)
- [ ] **T8.0b AI guardrails** (audit T3 BLOCKER, F-102/F-103) — *Verify:* guardrail suite green incl. AST no-execution guard
  - [ ] Schema-bound LLM outputs (Pydantic) with bounded repair retry; deterministic keyword fallback for news + template rationale (ADR-0001)
  - [ ] Kill switch: halts NEW cycles only; open signals keep resolving (Glossary semantics)
  - [ ] Guardrail tests: malformed LLM output, repair path, fallback path, kill-switch trip
- [ ] **T8.1 Degraded mode, retries, logging** (F-117) — *Verify:* failure-drill tests green; logs carry cycle_id
  - [ ] Per-dependency contract: market-data outage fails cycle (ADR-0002); RSS down → no news; TimesFM down → skip forecast; DB down → API 503, scheduler self-heals
  - [ ] Wire utils/retry.py at system edges (MT5, Anthropic, RSS, HTTP); no graph-node retries
  - [ ] Wire structlog: set_cycle_id at cycle start; replace print() in api/main.py + scripts; JSON stdout, level via env
  - [ ] Failure drills per dependency
- [ ] **T8.2 Backtest-lite** (smoke grade, not statistical proof) — *Verify:* replay produces report; threshold tests green
  - [ ] Replay data/real_fixtures through full graph with mocked LLM; Coulson resolves outcomes post-hoc
  - [ ] docs/backtest/BACKTEST_LITE_<date>.md: per-strategy win rate / avg RR / expectancy vs thresholds; thresholds asserted in tests
- [ ] **T8.3 Ops** — *Verify:* CI green from clean checkout; `jarvis --help` works
  - [ ] README run guide; minimal CI (pytest + ruff + mypy; mock-based tests, no MT5 on runner)
  - [ ] Real `jarvis` CLI (serve / scheduler / cycle) over existing scripts (fixes F-105)
  - [ ] Telegram alerts — P2, deferred
- [ ] **T8.4 2-week paper forward test** → review, tune weights — GATED, all six pre-flight checks hard:
  green baseline · guardrails · failure drills · MT5 UTC offset verified · tick-value semantics verified · formula review sign-off. Config frozen at start (config_snapshots, ADR-0003); no mid-test tuning except bug fixes; metrics per strategy + instrument; abort on 3+ consecutive failed cycles or kill-switch trip; RSS-only news accepted (limitation noted in report)