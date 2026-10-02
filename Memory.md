# Memory.md — Project Continuity (keep concise; newest first)

## Project snapshot
JARVIS: LangGraph multi-agent trade-signal system (MT5 read-only, TimesFM, news, 5 instruments, 5 strategies). Signals only, never executes. Supervisor = Jarvis.

## Current state
- Phase: 3 · Task: T3.1 · Last updated: 2026-10-02
- Environment: OS=Windows · Python=3.14.7 (uv project venv=3.14.5) · MT5 installed=yes · Broker symbols=standard/unchanged · Anthropic key location=C:\jarvis\.env (value not copied)

## Decisions log
| Date | Decision | Reason |
|------|----------|--------|
| — | Deterministic math, LLM only for news + rationale | Cost, accuracy, no hallucinated prices |
| — | Fan-out per instrument via LangGraph subgraphs | Parallel, isolated failures |
| 2026-10-02 | T1.2 defaults for sessions, ATR multipliers, strategy weights, score threshold, risk %, and cycle interval are provisional | Architecture/PRD do not specify these values |
| 2026-10-02 | T1.3 provider returns typed Candle/SymbolInfo/Tick models; fixture is synthetic, explicitly not recorded broker data; mock symbol info/tick must be injected | No broker sample or return shapes provided in Architecture.md |
| 2026-10-02 | T1.4 uses PyArrow-backed Parquet cache and fake MT5 API tests | Parquet engine absent before T1.4; added PyArrow |
| 2026-10-02 | T1.5 Vision returns per-symbol typed info, tick, and candle lists keyed by timeframe; candle count supplied by caller | Architecture defines fetch/validate behavior but not the Vision result contract or request size |
| 2026-10-02 | T2.1 implementations: Wilder ATR; EMA seeded at first value; strict swing pivots; close-cross BOS/CHoCH by prior trend; 3-candle wick FVG; opposite-color candle before displacement for order blocks; adjacent-price tolerance zones; Fib levels from explicit anchors | Project docs list indicators but do not specify formulas; implementations are deterministic conventions subject to later domain review |
| 2026-10-02 | T2.2 trend uses close vs configurable EMA; volatility regime uses configurable rolling ATR rank cutoffs; UTC session requires explicit configured windows or returns UNKNOWN | Project docs/config do not define trend/session/regime formulas or session hours |
| 2026-10-02 | T2.3 sizing requires explicit equity, ATR, and broker SymbolInfo/Tick; lot size derives from broker tick value/size and floors to volume step; below-minimum lots invalidate rather than exceed risk | Docs require risk sizing but do not specify sizing formula, ATR bounds, or spread cap |
| 2026-10-02 | T2.1 indicator conventions: Wilder ATR, first-value-seeded EMA, strict left/right swing pivots, close-cross BOS/CHoCH, three-candle FVG, opposite-candle displacement order block, tolerance-clustered zones, explicit-anchor Fib | Docs name indicators but do not specify formulas; conventions are implementation assumptions |

## Installed resources (name · source · version · date)
- uv · pre-installed locally; source not verified · 0.11.15 · 2026-10-01
- Python · pre-installed locally · 3.14.7 · 2026-10-01
- Git · pre-installed locally · 2.55.0 · 2026-10-01
- Node.js · pre-installed locally · 24.21.0 · 2026-10-01
- Ruff · pre-installed locally · 0.15.10 · 2026-10-01
- pytest · PyPI, initial uv runner cache · 9.0.2 · 2026-10-01
- pluggy · PyPI, initial uv runner cache · 1.6.0 · 2026-10-01
- anyio · PyPI, initial uv runner cache · 4.12.1 · 2026-10-01
- pytest-asyncio · PyPI, initial uv runner cache · 1.3.0 · 2026-10-01
- pytest-timeout · PyPI, initial uv runner cache · 2.4.0 · 2026-10-01
- mypy · PyPI (`https://pypi.org/simple`) · 2.3.1 · 2026-10-01
- ast-serialize · PyPI (`https://pypi.org/simple`) · 0.11.2 · 2026-10-01
- librt · PyPI (`https://pypi.org/simple`) · 0.16.0 · 2026-10-01
- mypy-extensions · PyPI (`https://pypi.org/simple`) · 1.1.0 · 2026-10-01
- pathspec · PyPI (`https://pypi.org/simple`) · 1.1.1 · 2026-10-01
- typing-extensions · PyPI (`https://pypi.org/simple`) · 4.16.0 · 2026-10-01
- langgraph · PyPI · 1.2.12 · 2026-10-01
- langchain-anthropic · PyPI · 1.7.5 · 2026-10-01
- pydantic · PyPI · 2.13.5 · 2026-10-01
- pydantic-settings · PyPI · 2.15.0 · 2026-10-01
- PyYAML · PyPI · 6.0.3 · 2026-10-01
- pandas · PyPI · 3.0.6 · 2026-10-01
- numpy · PyPI · 2.5.3 (2.4.6 for Python 3.11 per lock markers) · 2026-10-01
- ta · PyPI · 0.11.0 · 2026-10-01
- MetaTrader5 · PyPI · 5.0.6231 · 2026-10-01
- timesfm · PyPI; official API verified in google-research/timesfm · 3.0.2 · 2026-10-01
- torch · PyTorch CPU index (`https://download.pytorch.org/whl/cpu`) · 2.14.1+cpu · 2026-10-01
- feedparser · PyPI · 6.0.14 · 2026-10-01
- httpx · PyPI · 0.28.1 · 2026-10-01
- sqlmodel · PyPI · 0.0.47 · 2026-10-01
- APScheduler · PyPI · 3.11.3 · 2026-10-01
- fastapi · PyPI · 0.142.2 · 2026-10-01
- uvicorn · PyPI · 0.54.0 · 2026-10-01
- structlog · PyPI · 26.1.0 · 2026-10-01
- pytest · PyPI · 9.1.1 · 2026-10-01
- pytest-cov · PyPI · 7.1.0 · 2026-10-01
- ruff · PyPI · 0.16.10 · 2026-10-01
- @upstash/context7-mcp · npm registry (`https://registry.npmjs.org`) · 4.1.1; Claude MCP connected · 2026-10-01
- frontend-design · anthropics/skills commit `8a1541c4a3ffa5a20a5a91de0dcf3f0bab1d1ef4` · installed to user skills · 2026-10-01
- Python dependency closure · PyPI + PyTorch CPU index · 98 packages resolved; exact lock in `uv.lock` · 2026-10-01
- Frontend dependencies · npm registry · exact `web/package.json` pins installed and listed by `npm ls --depth=0`; Node 24.21.0 / npm 11.19.0 · 2026-10-02

## Progress log
- 2026-10-01 · T0.1 DONE: scaffold/config created; pytest, Ruff, strict mypy passed; commit `df7527d`.
- 2026-10-02 · T0.2 DONE: frontend installed with exact pins after extending npm fetch timeout; `npm ls --depth=0`, pytest (1 passed), Ruff, and mypy passed. Context7 was previously Connected; two latest health checks timed out (intermittent).
- Frontend install root cause: slow Vite tarball fetch; `npm install --prefer-online --fetch-timeout=600000 --fetch-retries=1` completed successfully without changing versions.
- 2026-10-02 · T0.3 DONE: existing 5-line `CLAUDE.md` pointer links required project documents; no change required. Next: Phase 1 T1.1 schemas and unit tests.
- 2026-10-02 · T1.1 DONE: added six Architecture.md §5 Pydantic models and contract tests; pytest 7 passed, Ruff and strict mypy clean. Next: T1.2 config loaders.
- 2026-10-02 · T1.2 DONE: added strict Pydantic config models, safe YAML loaders and three configs; pytest 13 passed, Ruff and strict mypy clean. Instrument sessions/ATR multipliers and strategy params are empty; weights and unspecified Jarvis score/risk/cycle defaults are provisional. Next: T1.3.
- 2026-10-02 · T1.3 DONE: added typed Candle/SymbolInfo/Tick, DataProvider Protocol, CSV MockProvider, and synthetic sample fixture. Pytest 19 passed; Ruff/mypy clean; no MT5/order API calls added. No real broker sample data was available. Next: T1.4.
- 2026-10-02 · T1.4 DONE: read-only MT5 provider, UTC mapping/validation, atomic Parquet cache via PyArrow 25.0.1; pytest 28 passed, Ruff/mypy clean. Live XAUUSD M15 fetch succeeded and produced cache; removed the cache file after verification so market data is not retained. Next: T1.5.
- 2026-10-02 · T1.5 DONE: added typed Vision result and provider-driven fetch for configured symbols/timeframes; pytest 32 passed, Ruff/mypy clean, execution/MT5 safety search clean. Next: T1.6.
- 2026-10-02 · T1.6 DONE: added AST/token no-execution guard; scanner tests cover direct/import/dynamic violations and allowed MT5 reads. Full suite: 36 passed; Ruff/mypy clean; production audit found no forbidden APIs. Next: T2.1.
- 2026-10-02 · T2.1 DONE: added typed indicator outputs and pure ATR, EMA, swings, BOS/CHoCH, FVG, order blocks, price zones, and Fibonacci retracements. Full suite 44 passed; Ruff/mypy clean; no-execution tests 4 passed. Formula conventions above remain subject to domain review. Next: T2.2.
- 2026-10-02 · T2.2 DONE: implemented Doctor Strange MTF trend/ATR, primary structure and key levels, tie-aware ATR-rank volatility regime, and explicit UTC session windows. Full suite 51 passed; Ruff/mypy clean; no-execution tests 4 passed. Conventions remain reviewable assumptions. Next: T2.3.
- 2026-10-02 · T2.3 DONE: added pure War Machine directional RR/ATR/spread checks and risk-based lot sizing from explicit equity and broker tick/volume metadata. Full suite 61 passed; Ruff/mypy clean; no-execution tests 4 passed. ATR bounds/spread cap stay required settings; broker tick-value account semantics still require user/broker verification. Next: T3.1.

## Open questions / UNVERIFIED items
- Context7 health checks timed out twice on 2026-10-02 after a prior successful Connected status; installed state remains, latest health unverified.
- News feed URLs live check

## Bugs & fixes
_(symptom · root cause · fix · test added)_

## Notes for next session
Begin T3.1 BaseStrategy + registry per Task.md; T2.1/T2.2 formulas and broker tick-value account semantics remain reviewable assumptions.
