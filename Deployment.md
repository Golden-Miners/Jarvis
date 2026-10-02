# Deployment — JARVIS

## 1. Target environments
| Env | Where | Data | Notes |
|-----|-------|------|-------|
| dev | Your PC | MockProvider or demo MT5 | hot reload |
| paper (primary prod) | Windows PC or Windows VPS with MT5 terminal logged in (demo or live, **investor password**) | real market data, no execution | forward test |
Reality check: the `MetaTrader5` Python package needs the MT5 terminal running on **Windows**. So the Jarvis backend runs on the same Windows machine. Dashboard can be served from the same host. Docker is optional for API/web only if MT5 data is fetched via a bridge **VERIFY**; default is native Windows (simplest, fewest failure points).

## 2. Prerequisites
Windows 10/11 or Server 2019+, MT5 terminal installed & logged in, Market Watch contains the 5 symbols, Python 3.11+, `uv`, Node 20+ (build only), Anthropic API key, ≥8 GB RAM (TimesFM CPU), ~5 GB disk.

## 3. Configuration
- `.env` from `.env.example` (Backend/API doc §8). `APP_ENV=prod`.
- `config/instruments.yaml`: set broker symbol names (e.g. `XAUUSD`, `XAUUSD.m`), digits, broker→UTC offset.
- `config/jarvis.yaml`: thresholds, weights, risk %, cycle interval, model IDs, token ceilings, `fail_closed_on_news`.
- Validate: `uv run jarvis config check` (must print OK).

## 4. First-time install
```
git clone <repo> && cd jarvis
uv sync
cd web && npm ci && npm run build && cd ..
uv run jarvis db upgrade && uv run jarvis db seed
uv run jarvis doctor        # checks MT5 connect, symbols, API key, TimesFM load, DB, disk
uv run jarvis run --once    # single cycle smoke test
```
`jarvis doctor` must be all-green before enabling the scheduler.

## 5. Running as a service (Windows)
- Process: `uv run jarvis serve` (FastAPI + scheduler, serves built `web/dist`, binds 127.0.0.1:8000).
- Keep alive via **NSSM** or Task Scheduler ("at startup", restart on failure, run whether user logged on or not — MT5 terminal must also auto-start and stay logged in).
- Auto-start order: MT5 terminal → Jarvis service.
- Remote viewing: Tailscale or Cloudflare Tunnel + Access (never open the port publicly). HTTPS terminates at the tunnel/reverse proxy (Caddy).

## 6. CI/CD (GitHub Actions, P1)
Pipeline on PR: `ruff` → `mypy` → `pytest` (MockProvider, no live LLM/MT5) → no-execution grep test → `gitleaks` → `pip-audit`/`npm audit` → web build + lint. On tag `vX.Y.Z`: build artifact (wheel + `web/dist`), attach to release. Deploy = manual pull on the host (`git fetch && git checkout vX.Y.Z && uv sync && jarvis db upgrade && restart service`). No auto-deploy to the machine holding MT5 credentials.

## 7. Release checklist
[ ] All tests green [ ] Migrations tested up/down on a copy of prod DB [ ] `jarvis doctor` OK on host [ ] Config diff reviewed [ ] Backup taken [ ] Memory.md/Task.md updated [ ] Tag created [ ] Post-deploy: one manual cycle, dashboard loads, SSE live.

## 8. Rollback
Stop service → `git checkout <previous tag>` → `uv sync` → restore DB backup only if migration was destructive (`jarvis db downgrade` preferred) → start service → verify cycle. Target < 10 min.

## 9. Monitoring & alerting
- `/api/v1/health` + `jarvis doctor` each hour (scheduler self-check).
- Dashboard status ring + degraded banner; optional Telegram alerts for: MT5 disconnected >2 cycles, cycle FAILED ×2, LLM auth failure, disk <1 GB, DB backup failed.
- Metrics logged per cycle: duration, per-agent latency, tokens, signals count, degraded flags. Weekly review of cost (tokens) and calibration (AI_Guardrails §7).
- Logs: `logs/jarvis.jsonl`, rotated daily, 14 days kept.

## 10. Backup & recovery
Nightly SQLite `.backup` (14 kept), weekly off-machine copy (encrypted); candles are re-fetchable from MT5 (back up config + DB primarily). Restore drill monthly: stop → replace DB → `jarvis db upgrade` → start → `doctor`.

## 11. Performance & cost targets
Full 5-symbol cycle < 60 s; TimesFM inference < 20 s total (CPU); LLM spend capped by daily token ceiling (default aimed at a few cents/day: 1 batched news call + ≤5 short rationale calls per cycle, only when TRADE or notable).

## 12. Operational runbook (common issues)
| Symptom | Likely cause | Action |
|---------|--------------|--------|
| `MT5_NOT_CONNECTED` | Terminal closed / logged out | Start MT5, log in, restart service |
| `MT5_SYMBOL_MISSING` | Wrong broker symbol | Fix `instruments.yaml`, add to Market Watch |
| `MT5_STALE_DATA` | Market closed / feed lag | Expected on weekends; else check broker |
| All NO_TRADE `DEGRADED:NEWS` | Feeds down + fail-closed | Check feeds, or temporarily set `fail_closed_on_news: false` (audited) |
| `LLM_BUDGET` | Token ceiling hit | Raise ceiling or wait; system continues deterministic |
| Slow cycles | TimesFM on weak CPU | Reduce context_len/horizon or symbols per TF |

## 13. Scaling path (later)
Move DB to PostgreSQL; move Jarvis to a Windows VPS near the broker server; run API/web in Docker behind Caddy while only the data-collector runs on Windows; add Redis queue if multi-user. Not needed for single-user v1.
