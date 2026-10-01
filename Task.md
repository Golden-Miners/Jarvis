# Task.md — Plan & Status
Status: `TODO` · `IN_PROGRESS` · `DONE` · `BLOCKED`. Update after every task. Priority P0 > P1 > P2.

## Phase 0 — Setup & Tooling (P0)
- [x] T0.1 Init repo, uv, pyproject, folder structure, .gitignore, .env.example, ruff/mypy/pytest config — *Verify:* `uv run pytest`, Ruff, and mypy pass
- [ ] T0.2 Install & verify dev resources (Context7 MCP, frontend-design skill, optional Superpowers plugin; Python libs) and log versions in Memory.md — *Verify:* `pip list`/`claude mcp list`
- [ ] T0.3 Create CLAUDE.md pointer (≤30 lines) — *Verify:* file exists, links docs

## Phase 1 — Core Contracts & Data (P0)
- [ ] T1.1 Pydantic schemas + unit tests
- [ ] T1.2 Config loaders (instruments/strategies/jarvis YAML)
- [ ] T1.3 DataProvider interface + MockProvider + fixtures (record sample candles)
- [ ] T1.4 MT5Provider (read-only) + cache + data validation — *Verify:* fetches XAUUSD M15 on user's machine
- [ ] T1.5 Vision agent
- [ ] T1.6 No-execution safety test

## Phase 2 — Analysis Engine (P0)
- [ ] T2.1 Indicators: ATR, EMA, swings, BOS/CHoCH, FVG, order block, zones, Fib (+tests)
- [ ] T2.2 Doctor Strange (structure/MTF/session/volatility regime)
- [ ] T2.3 War Machine (RR, ATR bounds, spread, lot suggestion)

## Phase 3 — Strategy Agents (P0) *(parallelisable)*
- [ ] T3.1 BaseStrategy + registry
- [ ] T3.2 Hawkeye (SMC/ICT)
- [ ] T3.3 Black Widow (trend-pullback)
- [ ] T3.4 Falcon (breakout)
- [ ] T3.5 Ant-Man (mean reversion)
- [ ] T3.6 Wasp (supply-demand + Fib)

## Phase 4 — Instrument Agents & Graph (P0)
- [ ] T4.1 Instrument base + 5 profiles (Iron Man, Captain America, Thor, Hulk, Black Panther)
- [ ] T4.2 Instrument subgraph (Strange → strategies parallel → merge → War Machine)
- [ ] T4.3 Main graph with fan-out per instrument + node error wrapper
- [ ] T4.4 Jarvis supervisor scoring + rationale (LLM, schema-constrained) — *Verify:* integration test on MockProvider yields valid Signals

## Phase 5 — News & Forecast (P1)
- [ ] T5.1 Nick Fury: feeds, calendar, impact classification, blackout logic
- [ ] T5.2 Quicksilver: TimesFM loader + forecast → `Forecast`
- [ ] T5.3 Wire both into graph + scoring weights

## Phase 6 — Persistence, API, Scheduler (P0/P1)
- [ ] T6.1 SQLite store + Coulson outcome tracker (P1)
- [ ] T6.2 FastAPI + SSE endpoints (P0)
- [ ] T6.3 Scheduler on M15 close + manual run (P0)

## Phase 7 — Dashboard (P0)
- [ ] T7.1 Scaffold web (Vite/React/TS/Tailwind) + design tokens from Design.md
- [ ] T7.2 Components + Signals/Agents/News views
- [ ] T7.3 History + Stats views, SSE live updates, responsive polish

## Phase 8 — Hardening & Forward Test (P1)
- [ ] T8.1 Degraded-mode tests, retries, logging
- [ ] T8.2 Backtest-lite replay on recorded data to sanity check thresholds
- [ ] T8.3 README (run guide), Telegram alerts (P2)
- [ ] T8.4 2-week paper forward-test review → tune weights

## Current focus
Phase 0 → T0.2
