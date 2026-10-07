# Fix Plan

## Tier 0 — Make the project runnable and testable
- **F-104 (ModuleNotFoundError: jarvis)**
  - **Severity:** BLOCKER
  - **Lane:** 6, 8
  - **Root Cause:** `pyproject.toml` lacks `[build-system]` and `jarvis` CLI entry point.
  - **Fix:** Add `build-system` to `pyproject.toml` (hatchling), add `jarvis` CLI script entrypoint, and run `uv sync`.
  - **Test:** Run `uv run python -c "import jarvis"` and `uv run jarvis --help`.
  - **Spec Reference:** Deployment.md (for CLI presence).
  - **Status:** FIXED

- **F-101 (Hanging commands/tests)**
  - **Severity:** BLOCKER
  - **Lane:** 1
  - **Root Cause:** Tests loading `timesfm` or doing network/heavy tasks are slow, and lack per-test timeouts or slow markers.
  - **Fix:** Add global per-test timeout (`pytest-timeout`). Mock network/heavy `timesfm` loads or mark them `@pytest.mark.slow`. Ensure default `pytest` finishes quickly. Fix ruff lint errors (unused imports, long lines).
  - **Test:** `uv run pytest -m "not slow" --durations=20`.
  - **Spec Reference:** N/A (General/Env).
  - **Status:** FIXED

## Tier 1 — Safety and security BLOCKERS
- **F-109 (VIEWER can reach rate-limited/OWNER endpoints)**
  - **Severity:** HIGH
  - **Lane:** 7
  - **Root Cause:** Rate limiter is evaluated before auth middleware, or `require_role` is missing.
  - **Fix:** Enforce `require_role` on every route. Move auth checks before rate limiting. Add endpoint test.
  - **Test:** Test each endpoint asserting 401/403 for lower roles.
  - **Spec Reference:** Security_Access.md, API_Integrations.md.
  - **Status:** FIXED

- **F-111 (Login lockout & Auth hygiene)**
  - **Severity:** HIGH
  - **Lane:** 7
  - **Root Cause:** Lockout after 5 failed attempts is missing. Check argon2id, httpOnly SameSite cookies, and audit_log entries.
  - **Fix:** Implement lockout (15 min), ensure argon2id, httpOnly cookies, audit_log entries.
  - **Test:** Fail login 5 times -> lockout.
  - **Spec Reference:** Security_Access.md, API_Integrations.md.
  - **Status:** FIXED

- **F-112 (.gitignore completeness)**
  - **Severity:** MEDIUM
  - **Lane:** 2
  - **Root Cause:** `.gitignore` missing `*.db`, `logs/`, etc.
  - **Fix:** Add them. Run `gitleaks` to check if a secret was ever committed.
  - **Test:** `git check-ignore` on `jarvis.db`.
  - **Spec Reference:** General/Security.
  - **Status:** FIXED

## Tier 2 — Data integrity
- **F-107 (Signal.confidence CHECK constraint)**
  - **Severity:** HIGH
  - **Lane:** 3
  - **Root Cause:** SQL CHECK between 0 and 1 missing, Pydantic `le=1.0` removed.
  - **Fix:** Add SQL CHECK constraint and Pydantic `le=1.0`. Add `score` as unbounded. Add reversible Alembic migration.
  - **Test:** Insert invalid confidence > 1 -> fails.
  - **Spec Reference:** Backend_Schema.md.
  - **Status:** FIXED

- **F-108 (Repository pattern violation in coulson.py)**
  - **Severity:** HIGH
  - **Lane:** 3
  - **Root Cause:** Agent uses `sqlmodel.Session` to insert records.
  - **Fix:** Move inserts to repository.
  - **Test:** Test that no agent module imports DB session directly.
  - **Spec Reference:** Backend_Schema.md.
  - **Status:** FIXED

- **Verify remaining constraints (F-116)**
  - **Severity:** HIGH
  - **Lane:** 3
  - **Root Cause:** Need invalid-insert tests for constraints.
  - **Fix:** Add invalid-insert tests (price ordering CHECK, NO_TRADE reason, etc.).
  - **Test:** Explicit invalid insert tests.
  - **Spec Reference:** Backend_Schema.md.
  - **Status:** FIXED

## Tier 3 — AI guardrails
- **F-102 & F-103 (LLM core logic, schema-bound, guardrail tests)**
  - **Severity:** BLOCKER
  - **Lane:** 4
  - **Root Cause:** LLM features (NewsImpactLLM, RationaleLLM) and missing tests.
  - **Fix:** Implement schema-bound outputs, repair retry, template fallback, unseen-number check, forbidden-phrase filter, prompt-injection handling, token budget, LLM kill switch. Implement guardrail test suite.
  - **Test:** Guardrail test suite (no live LLM).
  - **Spec Reference:** AI_Guardrails.md.
  - **Status:** TODO

## Tier 4 — API contract and robustness
- **F-113 & F-110 (Missing endpoints, custom error envelope)**
  - **Severity:** MEDIUM
  - **Lane:** 7
  - **Root Cause:** Config PATCH missing, default 422 returned.
  - **Fix:** Implement Config PATCH. Custom handler for FastAPI 422 validation errors to return `{error: {code, message, request_id}}`.
  - **Test:** Contract tests.
  - **Spec Reference:** API_Integrations.md.
  - **Status:** TODO

## Tier 5 — Failure drills and degraded mode
- **F-117 (Full-graph failure tests)**
  - **Severity:** HIGH
  - **Lane:** 6
  - **Root Cause:** No dedicated failure drill tests.
  - **Fix:** Add full-graph tests using MockProvider injected faults.
  - **Test:** Tests for MT5 disconnect, etc.
  - **Spec Reference:** Security_Access.md (6-8).
  - **Status:** TODO

## Tier 6 — Dashboard
- **F-114 (Copy signal button, Vitest tests)**
  - **Severity:** MEDIUM
  - **Lane:** 8
  - **Root Cause:** Missing feature, missing frontend tests, Playwright timeout.
  - **Fix:** Add "Copy signal" button, add Vitest tests, fix Playwright timeouts.
  - **Test:** Playwright tests, Vitest.
  - **Spec Reference:** Dashboard_Layout.md.
  - **Status:** TODO

## Tier 7 — Operations
- **F-105 & F-106 (jarvis CLI, README, CI workflow, .env.example)**
  - **Severity:** BLOCKER
  - **Lane:** 9
  - **Root Cause:** Ops tooling completely missing.
  - **Fix:** Build `jarvis` CLI commands. Complete `.env.example`. Write `README.md`. Setup GH Actions CI. Implement backup+restore drill logic and log rotation.
  - **Test:** Clean clone verification, `jarvis doctor`.
  - **Spec Reference:** Deployment.md.
  - **Status:** TODO

## Tier 8 — Items for a human
- **F-118 (Write docs/review/FORMULA_REVIEW.md)**
  - **Severity:** INFO
  - **Lane:** 8
  - **Root Cause:** Domain expert needs to review formulas.
  - **Fix:** Write `docs/review/FORMULA_REVIEW.md` listing formulas, assumptions, and provisional configs.
  - **Test:** N/A (Manual review).
  - **Spec Reference:** Memory.md.
  - **Status:** TODO
