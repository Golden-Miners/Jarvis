# API Integrations & Specifications — JARVIS

Rule: every external call goes through one adapter in `src/jarvis/integrations/` implementing a common interface, with timeout, retry, rate limit, and typed response. Agents never call third parties directly. Anything marked **VERIFY** must be checked against official docs (Context7/web) before coding — do not trust this document for endpoints/params.

## 0. Standard adapter contract
```python
class Adapter(Protocol):
    name: str
    def health(self) -> HealthStatus: ...
```
Defaults: connect timeout 5s, read timeout 15s, 3 retries (exp. backoff 1/2/4s + jitter) on 429/5xx/timeouts only, circuit breaker opens after 5 consecutive failures for 60s, structured log per call (service, op, status, latency_ms; no secrets/bodies). All responses validated by Pydantic; invalid → `IntegrationError(code)`.

## 1. Service register
| # | Service | Used by | Purpose | Auth | Cost | Required |
|---|---------|---------|---------|------|------|----------|
| 1 | MetaTrader 5 terminal (`MetaTrader5` Python pkg) | Vision | OHLCV, tick, symbol info (READ-ONLY) | Local terminal login | Free (broker account) | Yes |
| 2 | Anthropic API (Claude) | Nick Fury (Haiku), Jarvis (Sonnet) | News impact classification, rationale text | `ANTHROPIC_API_KEY` | Pay per token | Yes |
| 3 | TimesFM (google-research/timesfm, weights via Hugging Face Hub) | Quicksilver | Time-series quantile forecast | None (public weights) **VERIFY** | Free, local CPU/GPU | P1 |
| 4 | Economic calendar feed | Nick Fury | High-impact event times, blackout | **VERIFY** source (free JSON/ICS feeds vary; or Finnhub/FMP) | Free/low | P1 |
| 5 | News RSS feeds | Nick Fury | Headlines for metals/oil/crypto/macro | None | Free | P1 |
| 6 | Finnhub or NewsAPI (optional upgrade) | Nick Fury | Structured news | API key **VERIFY** limits | Free tier | P2 |
| 7 | Telegram Bot API | Alerts | Push signals to phone | `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` | Free | P2 |
| 8 | GitHub (Actions) | CI | Lint/test | Repo token | Free tier | P2 |

## 2. MetaTrader 5 (READ-ONLY)
- Allowed calls ONLY: `initialize`, `shutdown`, `last_error`, `copy_rates_from_pos`, `copy_rates_range`, `symbol_info`, `symbol_info_tick`, `symbol_select`, `terminal_info`. Verify exact names/signatures against MetaQuotes Python docs.
- Forbidden: `order_send`, `order_check`, `order_calc_*` writes, `positions_*`/`history_orders_*` mutation, anything that trades. CI test fails if found.
- Platform: Windows-native. Mac/Linux → Wine + bridge **VERIFY**; use `MockProvider` otherwise.
- Config: `MT5_PATH` (optional), `MT5_LOGIN`, `MT5_PASSWORD`, `MT5_SERVER` in `.env`. Prefer attaching to an already logged-in terminal; use an **investor (read-only) password** where possible.
- Timeframes: M5, M15, H1, H4, D1 → map to MT5 constants in one place.
- Output contract → DataFrame columns: `time(UTC), open, high, low, close, tick_volume, spread`. Timezone: MT5 server time ≠ UTC; convert using broker offset in config (**VERIFY with live data**).
- Failure modes: terminal not running, symbol not in Market Watch (`symbol_select`), market closed (stale last bar), weekend gap. Each maps to an `IntegrationError` code: `MT5_NOT_CONNECTED`, `MT5_SYMBOL_MISSING`, `MT5_STALE_DATA`.
- Rate: poll on new-bar only; one batch per cycle (≈5 symbols × 5 TF).

## 3. Anthropic API
- SDK: `anthropic` / `langchain-anthropic`. Check current model IDs from the official docs (**VERIFY**), store in `config/jarvis.yaml` (`models.news`, `models.supervisor`), never hardcode in agents.
- Usage: Nick Fury → small/fast model; Jarvis rationale → mid model. Temperature 0–0.2.
- Structured output: tool/JSON-schema bound to Pydantic (`NewsImpactLLM`, `RationaleLLM`). Invalid → 1 repair retry → fallback to template rationale / neutral news.
- Budget guard: `max_tokens` per call (news 400, rationale 500); daily token ceiling in config; at ceiling → LLM calls skipped, system runs deterministic-only (flagged `DEGRADED:LLM_BUDGET`).
- Prompt caching/batching: batch headlines in a single call per cycle (not per headline); cache classification by `url_hash`.
- Data sent: headlines + structured numbers only. Never keys, never account data.
- Errors: 401 → fatal config error (alert); 429/529 → backoff; timeout → degrade.

## 4. TimesFM
- Source: official google-research/timesfm repo/README **VERIFY** current package name, version, checkpoint ID, and call signature (`forecast` API changed between versions).
- Load once at startup (lazy singleton); weights cached in `data/models/`; CPU fallback; log load time.
- Input: last 512 closes (config `context_len`) per symbol/timeframe, float32, no NaN. Output: horizon 32 bars, point + quantiles → `Forecast`.
- Guard: if inference > 20s or exception → `Forecast=None`, Jarvis proceeds without it (weight redistributed).
- Test: deterministic fixture → shape/NaN assertions; no accuracy assertions.

## 5. News & calendar
- RSS via `feedparser`. Feed list in `config/news_sources.yaml` (name, url, tags[]). **VERIFY every URL returns valid XML before adding.** Respect each site's ToS/robots; poll ≤ once per 5 min with ETag/Last-Modified.
- Calendar: choose one verified source; normalise to `calendar_events` (name, currency, importance, time UTC). High importance → blackout `[-30, +30]` min (config). Currency→instrument map: USD affects XAU/XAG/USOUSD/BTC/ETH; EIA/OPEC → USOUSD; configurable.
- Dedupe by `url_hash`; drop items older than 24h; cap 50 items/cycle.
- Failure: any feed failing is skipped; all failing → `NewsImpact(impact=0, bias=NEUTRAL, summary="NEWS_UNAVAILABLE")` and `DEGRADED:NEWS`; Jarvis lowers confidence but does not trade through an unknown high-impact window if calendar also unavailable (config `fail_closed_on_news: true`).

## 6. Telegram (optional)
- `POST https://api.telegram.org/bot<TOKEN>/sendMessage` (**VERIFY** params). Message template: symbol, direction, entry/SL/TP, RR, confidence, 1-line why, "not financial advice". Send only on new `TRADE` signal; rate-limit 1 msg/sec; token in `.env`; chat ID allowlist.

## 7. Internal API (FastAPI) — specification
Base `/api/v1`, JSON, UTC ISO-8601, pagination `?limit=&cursor=`, errors `{ "error": {"code","message","request_id"} }`.
| Method | Path | Role | Description |
|--------|------|------|-------------|
| GET | /health | public(local) | liveness + adapter health |
| GET | /signals | VIEWER+ | list, filters symbol/status/decision/date |
| GET | /signals/{id} | VIEWER+ | detail + verdicts + candidate + risk |
| GET | /instruments | VIEWER+ | config + latest decision per symbol |
| GET | /agents/status | VIEWER+ | last run, latency, health |
| GET | /news | VIEWER+ | latest items + impacts |
| GET | /calendar | VIEWER+ | upcoming events/blackouts |
| GET | /stats | VIEWER+ | win rate, avg R, expectancy by strategy/symbol |
| POST | /cycles/run | OWNER | trigger manual cycle (rate-limited 1/min) |
| PATCH | /config/instruments/{symbol} | OWNER | enable/disable |
| GET | /stream | VIEWER+ | SSE: `signal.created`, `signal.updated`, `cycle.status`, `agent.health` |
OpenAPI auto-generated; response models in `schemas/api.py`; contract tests via `schemathesis` or pytest.

## 8. Env vars (`.env.example`)
```
ANTHROPIC_API_KEY=
MT5_LOGIN= MT5_PASSWORD= MT5_SERVER= MT5_PATH=
TELEGRAM_BOT_TOKEN= TELEGRAM_CHAT_ID=
FINNHUB_API_KEY=
DATABASE_URL=sqlite:///data/jarvis.db
JWT_SECRET= APP_ENV=dev
```

## 9. Integration verification checklist (per service, before marking done)
[ ] Official doc consulted (link in Memory.md) [ ] Adapter + Pydantic response model [ ] Timeout/retry/breaker [ ] Fixture-based unit test + one live smoke test (manual) [ ] Failure-mode test [ ] Health check [ ] No secrets logged
