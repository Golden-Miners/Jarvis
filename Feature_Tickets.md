# Feature Ticket List — JARVIS
Format: ID · Title · Priority (P0 must / P1 should / P2 nice) · Phase (Task.md) · Depends · Acceptance Criteria (AC). Status: TODO/IN_PROGRESS/DONE/BLOCKED. Keep in sync with Task.md.

## Epic A — Foundation
| ID | Title | P | Ph | Dep | Acceptance criteria | Status |
|----|-------|---|----|-----|---------------------|--------|
| J-001 | Repo scaffold & tooling | P0 | 0 | — | uv/pyproject, ruff, mypy, pytest run clean; folder tree matches Architecture §4 | TODO |
| J-002 | Resource install & log | P0 | 0 | J-001 | Context7, frontend-design skill (+optional Superpowers) verified & installed; versions in Memory.md | TODO |
| J-003 | Config system | P0 | 1 | J-001 | YAML for instruments/strategies/jarvis validated by Pydantic; invalid config fails fast with `CONFIG_INVALID` | TODO |
| J-004 | Pydantic schemas | P0 | 1 | J-001 | All models in Architecture §5 + validators (BUY: SL<entry<TP) with tests | TODO |
| J-005 | DB layer & migrations | P0 | 1 | J-004 | Tables per Backend_Schema; Alembic upgrade/downgrade; CHECK constraints tested | TODO |
| J-006 | Structured logging & error types | P0 | 1 | J-001 | JSON logs w/ cycle_id; error codes per Security_Access §7; secrets redacted | TODO |

## Epic B — Data
| ID | Title | P | Ph | Dep | AC | Status |
|----|-------|---|----|-----|----|--------|
| J-010 | DataProvider interface + MockProvider | P0 | 1 | J-004 | Replays fixture candles for all 5 symbols × 5 TF | TODO |
| J-011 | MT5Provider (read-only) | P0 | 1 | J-010 | Fetches XAUUSD M15 live; only allowed MT5 calls; timezone offset handled | TODO |
| J-012 | Candle cache & validation | P0 | 1 | J-011 | Parquet cache, new-bar refresh, invalid data → STALE | TODO |
| J-013 | Vision agent | P0 | 1 | J-012 | Returns validated candle bundle + symbol health; graph node | TODO |
| J-014 | No-execution safety test | P0 | 1 | J-011 | CI fails if forbidden MT5/trade function appears | TODO |

## Epic C — Analysis
| ID | Title | P | Ph | Dep | AC | Status |
|----|-------|---|----|-----|----|--------|
| J-020 | Indicator library | P0 | 2 | J-004 | ATR, EMA, swings, BOS/CHoCH, FVG, OB, zones, Fib; ≥80% coverage | TODO |
| J-021 | Doctor Strange (structure/MTF) | P0 | 2 | J-020 | `MarketStructure` per symbol incl. session & volatility regime | TODO |
| J-022 | War Machine (risk) | P0 | 2 | J-004 | RR, ATR-bounds, spread, lot suggestion; invalid reasons listed | TODO |

## Epic D — Strategies
| ID | Title | P | Ph | Dep | AC | Status |
|----|-------|---|----|-----|----|--------|
| J-030 | BaseStrategy + registry | P0 | 3 | J-020 | Plug-in via strategies.yaml; weights/params from config | TODO |
| J-031 | Hawkeye — SMC/ICT | P0 | 3 | J-030 | Liquidity sweep + OB/FVG setups with SL/TP; fixture tests with known setups | TODO |
| J-032 | Black Widow — trend pullback | P0 | 3 | J-030 | EMA/structure pullback entries | TODO |
| J-033 | Falcon — breakout/momentum | P0 | 3 | J-030 | Range break + volatility filter | TODO |
| J-034 | Ant-Man — mean reversion | P1 | 3 | J-030 | Range-regime-only; disabled in strong trend | TODO |
| J-035 | Wasp — supply/demand + Fib | P1 | 3 | J-030 | Zone retest + Fib confluence | TODO |

## Epic E — Instruments & Graph
| ID | Title | P | Ph | Dep | AC | Status |
|----|-------|---|----|-----|----|--------|
| J-040 | Instrument agent base + Iron Man (XAUUSD) | P0 | 4 | J-021,J-030 | Profile-driven (sessions, ATR mult, enabled strategies); first end-to-end on gold | TODO |
| J-041 | Captain America, Thor, Hulk, Black Panther | P1 | 4 | J-040 | Added via config + profile; 24/7 handling for crypto, EIA awareness for oil | TODO |
| J-042 | Instrument subgraph | P0 | 4 | J-040 | Strange ‖ strategies parallel → merge → War Machine | TODO |
| J-043 | Main graph fan-out & node error wrapper | P0 | 4 | J-042 | Per-symbol isolation; failure in one symbol doesn't affect others | TODO |
| J-044 | Jarvis supervisor | P0 | 4 | J-043 | Scoring + hard gates (AI_Guardrails §4); NO_TRADE reason codes; valid `Signal` | TODO |
| J-045 | Rationale generator (LLM + fallback) | P1 | 4 | J-044 | Schema-bound; number-hallucination check; template fallback | TODO |

## Epic F — News & Forecast
| ID | Title | P | Ph | Dep | AC | Status |
|----|-------|---|----|-----|----|--------|
| J-050 | News adapters (RSS + calendar) | P1 | 5 | J-006 | Verified feeds; dedupe; ETag; failure-tolerant | TODO |
| J-051 | Nick Fury impact classifier | P1 | 5 | J-050 | Batched LLM call, schema output, injection test passes, cached | TODO |
| J-052 | Blackout engine | P1 | 5 | J-050 | High-impact events create ±N min windows; Jarvis honours | TODO |
| J-053 | Quicksilver (TimesFM) | P1 | 5 | J-013 | Model loads once; `Forecast` for 5 symbols; failure → None | TODO |
| J-054 | Wire news & forecast into scoring | P1 | 5 | J-044,J-051,J-053 | Weights from config; forecast weight cap enforced | TODO |

## Epic G — Persistence, API, Scheduling
| ID | Title | P | Ph | Dep | AC | Status |
|----|-------|---|----|-----|----|--------|
| J-060 | Repositories & signal store | P0 | 6 | J-005 | Agents never touch SQL; unique OPEN signal index works | TODO |
| J-061 | Coulson outcome tracker | P1 | 6 | J-060 | Detects TP/SL/expiry from later candles; writes `outcomes` + R-multiple | TODO |
| J-062 | FastAPI endpoints | P0 | 6 | J-060 | All routes in API_Integrations §7; OpenAPI; role checks | TODO |
| J-063 | SSE stream | P0 | 6 | J-062 | Dashboard receives `signal.created` within 1s | TODO |
| J-064 | Scheduler (M15 close) + manual run | P0 | 6 | J-043 | No overlapping cycles; manual run rate-limited | TODO |
| J-065 | Auth & roles | P0 | 6 | J-062 | OWNER/VIEWER enforced; lockout; audit entries | TODO |

## Epic H — Dashboard
| ID | Title | P | Ph | Dep | AC | Status |
|----|-------|---|----|-----|----|--------|
| J-070 | Web scaffold + design tokens | P0 | 7 | J-062 | Vite/React/TS/Tailwind; tokens exactly per Design.md | TODO |
| J-071 | Instrument tiles + signal cards | P0 | 7 | J-070 | Entry/SL/TP, RR, confidence ring, expandable "Why" | TODO |
| J-072 | Agent roster & health | P1 | 7 | J-070 | Status dot, latency, last run | TODO |
| J-073 | News & macro panel | P1 | 7 | J-070 | Impact meter, events, blackout badges | TODO |
| J-074 | History & stats views | P1 | 7 | J-070 | Filters; win rate/avg R/expectancy as number cards (no charts) | TODO |
| J-075 | Live updates, skeletons, error boundaries, responsive | P0 | 7 | J-071 | SSE live; per-panel ErrorBoundary; mobile layout; AA contrast | TODO |
| J-076 | Dark/light theme | P2 | 7 | J-070 | Toggle persists | TODO |

## Epic I — Hardening & Ops
| ID | Title | P | Ph | Dep | AC | Status |
|----|-------|---|----|-----|----|--------|
| J-080 | Guardrail test suite | P0 | 8 | J-045,J-051 | All tests in AI_Guardrails §12 green | TODO |
| J-081 | Degraded-mode integration tests | P0 | 8 | J-043 | Each agent forced to fail → correct fallback/NO_TRADE | TODO |
| J-082 | Replay backtest-lite | P1 | 8 | J-044 | Runs graph over recorded history; outputs hit-rate/avg R per strategy | TODO |
| J-083 | Telegram alerts | P2 | 8 | J-062 | New TRADE signal → message with footer | TODO |
| J-084 | Trade journal (taken/skipped) | P2 | 8 | J-062 | Mark signals; stats include/exclude | TODO |
| J-085 | Packaging, CI, backups, runbook | P1 | 8 | all | Per Deployment.md | TODO |
| J-086 | 2-week paper forward test & tuning | P1 | 8 | J-085 | Report in Memory.md; weight changes logged | TODO |

## Release milestones
- **M1 (Gold MVP):** J-001..J-006, J-010..J-014, J-020..J-022, J-030..J-032, J-040, J-042..J-044, J-060, J-062..J-064 → console + API signals for XAUUSD.
- **M2 (Dashboard):** J-065, J-070..J-075.
- **M3 (All instruments + intelligence):** J-033..J-035, J-041, J-045, J-050..J-054, J-061.
- **M4 (Production-ready):** Epic I.
