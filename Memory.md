# Memory.md — Project Continuity (keep concise; newest first)

## Project snapshot
JARVIS: LangGraph multi-agent trade-signal system (MT5 read-only, TimesFM, news, 5 instruments, 5 strategies). Signals only, never executes. Supervisor = Jarvis.

## Current state
- Phase: 0 · Task: T0.2 · Last updated: 2026-10-01
- Environment: OS=Windows · Python=3.14.7 (uv project venv=3.14.5) · MT5 installed=yes · Broker symbols=standard/unchanged · Anthropic key location=C:\jarvis\.env (value not copied)

## Decisions log
| Date | Decision | Reason |
|------|----------|--------|
| — | Deterministic math, LLM only for news + rationale | Cost, accuracy, no hallucinated prices |
| — | Fan-out per instrument via LangGraph subgraphs | Parallel, isolated failures |

## Installed resources (name · source · version · date)
- uv · pre-installed locally; source not verified · 0.11.15 · 2026-10-01
- Python · pre-installed locally · 3.14.7 · 2026-10-01
- Git · pre-installed locally · 2.55.0 · 2026-10-01
- Node.js · pre-installed locally · 24.21.0 · 2026-10-01
- Ruff · pre-installed locally · 0.15.10 · 2026-10-01
- pytest · PyPI (uv default index; official metadata verified) · 9.0.2 · 2026-10-01
- pluggy · PyPI (uv default index) · 1.6.0 · 2026-10-01
- anyio · PyPI (uv default index) · 4.12.1 · 2026-10-01
- pytest-asyncio · PyPI (uv default index) · 1.3.0 · 2026-10-01
- pytest-timeout · PyPI (uv default index) · 2.4.0 · 2026-10-01
- mypy · PyPI (`https://pypi.org/simple`) · 2.3.1 · 2026-10-01
- ast-serialize · PyPI (`https://pypi.org/simple`) · 0.11.2 · 2026-10-01
- librt · PyPI (`https://pypi.org/simple`) · 0.16.0 · 2026-10-01
- mypy-extensions · PyPI (`https://pypi.org/simple`) · 1.1.0 · 2026-10-01
- pathspec · PyPI (`https://pypi.org/simple`) · 1.1.1 · 2026-10-01
- typing-extensions · PyPI (`https://pypi.org/simple`) · 4.16.0 · 2026-10-01

## Progress log
- 2026-10-01 · T0.1 DONE: scaffold/config created; `uv run pytest` 1 passed, Ruff passed, strict mypy passed; commit `443d6cb`.
- 2026-10-01 · T0.2 prerequisite: mypy 2.3.1 verified via official PyPI metadata and installed alone with required runtime dependencies; other T0.2 items remain untouched.
- `uv run pytest` initially auto-provisioned its runner before source verification; pytest metadata was subsequently verified against PyPI. No credentials were added.

## Open questions / UNVERIFIED items
- TimesFM package API/version (verify from official repo)
- News feed URLs live check

## Bugs & fixes
_(symptom · root cause · fix · test added)_

## Notes for next session
_(first thing to do next time)_
