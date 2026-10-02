# Security & Access — JARVIS

## 1. Threat model (short)
Assets: MT5 credentials, Anthropic key, signal history, config. Risks: secret leakage, unauthorised dashboard access, accidental trade-execution code, prompt injection via news, data corruption, runaway LLM cost. Default posture: **local-first, least privilege, fail closed.**

## 2. Roles & permissions
| Role | Who | Can |
|------|-----|-----|
| **OWNER** | You | Everything: view, trigger cycles, change config, enable/disable instruments, manage users, export data |
| **VIEWER** | Optional (partner/mentor) | Read signals, news, stats; no config, no triggers, no exports of raw logs |
| **SYSTEM** | Internal agents/scheduler | Write via repositories only; no API login; actions logged as `system:<agent>` |
Nobody (including OWNER and SYSTEM) can execute trades — the capability does not exist. Permission matrix is enforced by a FastAPI dependency `require_role(...)` on every route; tests assert each endpoint's required role.

## 3. Authentication
- Single-user mode default: API bound to `127.0.0.1`; OWNER login required anyway.
- Passwords hashed with argon2id (or bcrypt cost ≥12); JWT access token 15 min + refresh 7 days, `JWT_SECRET` ≥32 bytes from `.env`; httpOnly, SameSite=Strict cookies; CSRF token on state-changing requests.
- Lockout: 5 failed logins → 15 min delay. All auth events → `audit_log`.
- Remote access (if ever): only via VPN/Tailscale/Cloudflare Access + HTTPS; never expose port raw.

## 4. Secrets management
- `.env` (gitignored), file perms 600; `.env.example` has keys only. Pre-commit hook (`gitleaks`) blocks secrets.
- Rotate keys on suspicion; separate dev/prod keys; MT5 **investor password** preferred (read-only at broker level).
- Secrets never in logs, DB, prompts, error messages, or frontend bundle.

## 5. Data privacy rules
- Data is local; no telemetry. Only headlines + numeric market summaries go to the LLM — never credentials, account balance, login, or personal data.
- Account balance used for lot-size suggestion is read from user config (`risk.account_size`), not fetched from MT5 account info by default.
- Logs: redact tokens, emails, keys (central log filter). Retain per Backend_Schema §5.6.
- Exports (CSV) contain signals only; OWNER only.
- Third-party ToS respected (news scraping limits, attribution).

## 6. Error boundaries
Each boundary catches, logs, converts to a typed error, and degrades instead of crashing.
| Boundary | Catches | Result |
|----------|---------|--------|
| Integration adapter | network, auth, parse | `IntegrationError(code)` |
| Agent node wrapper | any exception in node | `AgentError` in state; node output = `None`; run continues |
| Subgraph (per instrument) | instrument-level failure | that symbol → `NO_TRADE: DEGRADED`; other symbols unaffected |
| Cycle runner | graph-level failure | cycle `FAILED`, alert, next cycle still scheduled |
| API layer | unhandled exception | 500 with `request_id`, no stack trace to client |
| UI | component error | React ErrorBoundary per panel; rest of dashboard works |

## 7. Error codes (stable, documented)
`MT5_NOT_CONNECTED, MT5_SYMBOL_MISSING, MT5_STALE_DATA, DATA_INVALID, LLM_TIMEOUT, LLM_SCHEMA_INVALID, LLM_BUDGET, NEWS_UNAVAILABLE, FORECAST_FAILED, RISK_INVALID, DB_WRITE_FAILED, CONFIG_INVALID, AUTH_FAILED, FORBIDDEN, RATE_LIMITED, INTERNAL`.

## 8. Error-handling protocol
1. **Detect** (exception/validation). 2. **Classify** (transient vs permanent). 3. **Retry** transient only (≤3, backoff). 4. **Degrade**: continue without that input; Jarvis lowers confidence or returns `NO_TRADE` with `DEGRADED:<code>`. 5. **Record**: `agent_runs` row + structured log with `cycle_id`, `request_id`. 6. **Alert** on: MT5 down >2 cycles, LLM auth failure, DB write failure, cycle FAILED ×2 (dashboard banner + optional Telegram). 7. **Never** fabricate data, guess prices, or swallow errors silently.
Fail-closed cases (force NO_TRADE): stale/invalid candles, risk agent error, unknown high-impact news window (if configured), DB unavailable.

## 9. Application hardening
- Input validation via Pydantic on all endpoints; parameterised queries only (ORM/repositories).
- CORS allowlist = dashboard origin only; security headers (CSP, X-Content-Type-Options, frame deny).
- Rate limits: 60 req/min per IP (read), `/cycles/run` 1/min.
- Dependency hygiene: `uv lock`/`npm audit`/`pip-audit` in CI; pin versions; Dependabot.
- No-execution guard: CI test greps for forbidden MT5 functions; code review rule.
- Prompt-injection defence: see AI_Guardrails.md.

## 10. Auditing
`audit_log` records: logins, config changes, manual runs, user changes, exports, guardrail violations. Append-only, OWNER-readable.

## 11. Incident response
Suspected key leak → rotate key, revoke sessions (`JWT_SECRET` change), review `audit_log`, check provider usage dashboards. Corrupt DB → stop service, restore latest backup (Deployment.md), replay missed cycles not needed (signals are time-bound).
