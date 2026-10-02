# Memory.md — Project Continuity (keep concise; newest first)

## Project snapshot
JARVIS: LangGraph multi-agent trade-signal system (MT5 read-only, TimesFM, news, 5 instruments, 5 strategies). Signals only, never executes. Supervisor = Jarvis.

## Current state
- Phase: 1 · Task: T1.4 (BLOCKED: live XAUUSD M15 verification) · Last updated: 2026-10-02
- Environment: OS=Windows · Python=3.14.7 (uv project venv=3.14.5) · MT5 installed=yes · Broker symbols=standard/unchanged · Anthropic key location=C:\jarvis\.env (value not copied)

## Decisions log
| Date | Decision | Reason |
|------|----------|--------|
| — | Deterministic math, LLM only for news + rationale | Cost, accuracy, no hallucinated prices |
| — | Fan-out per instrument via LangGraph subgraphs | Parallel, isolated failures |
| 2026-10-02 | T1.2 defaults for sessions, ATR multipliers, strategy weights, score threshold, risk %, and cycle interval are provisional | Architecture/PRD do not specify these values |
| 2026-10-02 | T1.3 provider returns typed Candle/SymbolInfo/Tick models; fixture is synthetic, explicitly not recorded broker data; mock symbol info/tick must be injected | No broker sample or return shapes provided in Architecture.md |
| 2026-10-02 | T1.4 uses PyArrow-backed Parquet cache and fake MT5 API tests; live XAUUSD M15 verification is pending because no terminal is available | Parquet engine absent; `terminal_info()` returned None |

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
- 2026-10-02 · T1.4 implementation verified with fake API: read-only MT5 provider, UTC candle mapping/validation, atomic per-symbol/timeframe Parquet cache using PyArrow 25.0.1; pytest 28 passed, Ruff/mypy clean. Live XAUUSD M15 verification remains BLOCKED: terminal unavailable (`terminal_info()` None); corrected command was canceled.

## Open questions / UNVERIFIED items
- Context7 health checks timed out twice on 2026-10-02 after a prior successful Connected status; installed state remains, latest health unverified.
- News feed URLs live check

## Bugs & fixes
_(symptom · root cause · fix · test added)_

## Notes for next session
T1.4 code is committed/ready but blocked pending a live XAUUSD M15 fetch with the user's MT5 terminal; then resume T1.4 verification before T1.5.
