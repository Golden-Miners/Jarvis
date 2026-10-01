# Rules — AI Builder Rulebook for JARVIS

## 0. Read order (every session)
`CLAUDE.md` → `Memory.md` → `Task.md` → only the section of `Architecture.md`/`Design.md` needed for the current task. Do not read the whole repo.

## 1. Absolute prohibitions
- NEVER write code that places, modifies, closes or checks orders (`order_send`, `order_check`, `positions_*` writes, etc.). Signals only. Keep `tests/test_no_execution.py` green.
- NEVER invent APIs, package names, function signatures, URLs, versions, prices or market data. If unsure → check official docs (Context7 MCP / repo README / `pip show` / `--help`) or say "unverified" and ask.
- NEVER hardcode secrets or commit `.env`.
- NEVER fake/mock data in production paths. Mock only in `MockProvider` and tests, clearly labelled.
- NEVER let an LLM produce prices, SL, TP or RR. Numbers come from deterministic code.
- NEVER add dependencies, files or features outside the current Task.md item without noting it in Memory.md.

## 2. Zero-hallucination protocol
1. Before using any library: confirm it exists and check the installed version's API (`python -c "import x; help(x.y)"` or docs).
2. Before installing any plugin/skill/MCP/repo: confirm the exact name and source URL; install only from official/well-known sources; record in Memory.md.
3. Mark uncertain facts `UNVERIFIED:` in code comments/Memory.md and resolve them before the phase closes.
4. Prefer reading existing code over assuming it.
5. If a requirement is ambiguous, ask ONE concise question, then proceed with the safest default.

## 3. Token & context efficiency
- Use plan mode for each phase; get the plan approved before writing code.
- Work in small vertical slices (one agent/module + its tests per task).
- Don't paste large files back; use targeted `grep`/line-range reads and diffs.
- Don't re-explain or re-summarise finished work. Update Memory.md concisely (≤10 lines per entry).
- Use `/compact` at ~60% context; `/clear` between phases (state lives in Memory.md/Task.md).
- Use subagents only for independent, parallelisable work (e.g., 5 strategy agents).
- Run only the relevant tests during iteration; the full suite at phase end.
- Prefer the cheaper model for routine edits; reserve the strongest model for architecture/debug.

## 4. Development workflow (per task)
1. Pick next `TODO` item in Task.md → set `IN_PROGRESS`.
2. Write failing test (or fixture-based test) → implement → pass → `ruff` + `mypy`.
3. Verify with the verification step listed in the task (actually run it; show output).
4. Set `DONE` in Task.md; append progress to Memory.md; commit (`type(scope): message`).
Never claim "done/working" without running the verification command.

## 5. Coding rules
- Follow Architecture.md §12. All inter-agent data uses `schemas/` models; no raw dicts across nodes.
- Each agent = one file, one responsibility, pure `run(state) -> partial_state` function plus helpers.
- Strategy agents implement `BaseStrategy.analyse(ctx) -> list[SetupCandidate]`; no side effects, no network.
- Indicators are pure functions with unit tests on fixtures.
- Config via YAML + Pydantic settings; no magic numbers in code.
- Timezone: UTC internally; convert only in UI.
- Handle MT5 symbol suffix/digits/point from `symbol_info`; never assume 2 decimals.

## 6. Error & bug handling
- Wrap every node: catch → log structured error → append `AgentError` → continue degraded (never crash the graph, never silently swallow).
- Retries: network/MT5 calls max 3 with exponential backoff; no retry on validation errors.
- Bug protocol: reproduce → write failing test → find root cause (no guess-patching) → fix → run regression → note in Memory.md "Bugs & fixes".
- After 2 failed fix attempts, stop, summarise findings, and ask the user.
- Data sanity: reject candles with gaps/NaN/non-monotonic time; mark symbol `STALE` and skip signals.

## 7. Testing rules
- Unit: indicators, structure, each strategy (recorded fixtures), risk math, scoring.
- Integration: full graph on `MockProvider` produces valid `Signal`s; degraded-mode test (news agent fails).
- Safety: no-execution grep test; schema validation test for every signal.
- Coverage target ≥ 80% on `indicators/`, `agents/`, `graph/`.

## 8. UI rules
Follow Design.md exactly. Use the `frontend-design` skill for the dashboard. No charts. No placeholder lorem data in shipped UI — bind to the API.

## 9. Security & safety
- MT5 credentials only in `.env`; read-only usage.
- API binds to localhost by default.
- Every signal displays a "not financial advice" footer.

## 10. Definition of done (per phase)
All phase tasks DONE, tests green, ruff/mypy clean, Memory.md updated, Task.md statuses updated, demo command works.
