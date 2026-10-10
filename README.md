# JARVIS — Multi-Agent Trade Signal Intelligence

> **Read-only, signals only.** JARVIS never places, modifies or closes trades. It analyses market structure, news, and forecasts to produce actionable trade signals with entry/SL/TP, confidence, and rationale.

![Python](https://img.shields.io/badge/python-3.11+-blue)
![LangGraph](https://img.shields.io/badge/LangGraph-multi--agent-orange)
![MT5](https://img.shields.io/badge/MetaTrader5-read--only-green)
![FastAPI](https://img.shields.io/badge/FastAPI-SSE-teal)
![React](https://img.shields.io/badge/React-Vite%20%2B%20TS%20%2B%20Tailwind-61DAFB)

---

## What it does

JARVIS runs a **LangGraph multi-agent pipeline** every 15 minutes (on M15 candle close) or on demand:

1. **Vision** — fetches & validates OHLCV from MT5 (M5/M15/H1/H4/D1) with local parquet cache
2. **Nick Fury** — ingests news/calendar → impact score, bias, blackout windows
3. **Per-instrument subgraphs** (parallel):
   - **Doctor Strange** — multi-timeframe structure (swings, BOS/CHoCH, trend, S/R, ATR, volatility regime, session)
   - **Quicksilver** — TimesFM quantile forecasts (supporting input)
   - **5 Strategy agents** (parallel):
     - **Hawkeye** — SMC/ICT: liquidity sweeps, order blocks, FVG
     - **Black Widow** — trend + pullback (EMA/structure)
     - **Falcon** — breakout / momentum
     - **Ant-Man** — mean reversion / range
     - **Wasp** — supply-demand zones + Fibonacci
   - **War Machine** — risk validation: SL/TP, R:R ≥ 1.5, ATR sanity, spread cap, lot sizing from 1% risk
4. **Jarvis (supervisor)** — confluence scoring → **TRADE / NO_TRADE** + entry, SL, TP, RR, confidence, rationale
5. **Coulson** — persists signals to SQLite, tracks hypothetical outcomes (TP/SL hit first)
6. **Dashboard** — live signals, per-agent verdicts, news panel, history, performance stats (via SSE)

---

## Agent roster

| Agent | Role |
|-------|------|
| **Jarvis** | Supervisor — final confluence decision |
| **Vision** | MT5 ingestion, caching, validation |
| **Doctor Strange** | Market structure & multi-timeframe analysis |
| **Nick Fury** | News & macro impact |
| **Quicksilver** | TimesFM forecasting |
| **Iron Man** | XAUUSD instrument agent |
| **Captain America** | XAGUSD instrument agent |
| **Thor** | BTCUSD instrument agent |
| **Hulk** | ETHUSD instrument agent |
| **Black Panther** | USOUSD instrument agent |
| **Hawkeye** | Strategy: SMC/ICT (liquidity, OB, FVG) |
| **Black Widow** | Strategy: trend + pullback |
| **Falcon** | Strategy: breakout / momentum |
| **Ant-Man** | Strategy: mean reversion |
| **Wasp** | Strategy: supply-demand + Fibonacci |
| **War Machine** | Risk & SL/TP validation |
| **Coulson** | Signal logger & outcome tracker |

---

## Quick start

### Prerequisites
- Windows (MT5 terminal runs natively here)
- Python 3.11+ & [uv](https://github.com/astral-sh/uv)
- MetaTrader 5 terminal installed & logged in to a live/demo account
- Node.js 20+ & npm (for dashboard)

### 1. Configure
```bash
cd C:\jarvis
cp .env.example .env   # edit: ANTHROPIC_API_KEY, JWT_SECRET, MT5 path if non-default
```

Key config lives in `config/`:
- `instruments.yaml` — symbol map, broker symbols, sessions, ATR multipliers
- `strategies.yaml` — enabled strategies, weights, params
- `jarvis.yaml` — thresholds, risk %, cycle interval
- `risk.yaml` — SL/TP bounds, spread caps
- `sessions.yaml` — trading session windows

### 2. Install & run (API only)
```bash
uv sync
uv run python scripts/start_api.py
# API at http://127.0.0.1:5180
# Health: http://127.0.0.1:5180/api/v1/health
```

### 3. Run with scheduler (M15 cycles)
```bash
uv run python scripts/run_jarvis.py
# Starts API + internal APScheduler (cron: 0,15,30,45 min UTC)
```

### 4. Dashboard
```bash
cd web && npm install && npm run dev
# Frontend at http://localhost:5173 (proxies /api to :5180)
```

Default login: `admin` / `changeme` (change on first login).

---

## Project structure (abridged)

```
jarvis/
├── config/                 # YAML: instruments, strategies, risk, sessions, jarvis
├── src/jarvis/
│   ├── agents/             # Vision, Strange, Fury, Quicksilver, Jarvis, WarMachine, Coulson
│   │   ├── instruments/    # One class per instrument (IronMan, CaptainAmerica, ...)
│   │   └── strategies/     # Hawkeye, BlackWidow, Falcon, AntMan, Wasp
│   ├── data/               # MT5Provider, cache, schemas
│   ├── indicators/         # ATR, EMA, swings, FVG, OB, Fib, zones
│   ├── graph/              # LangGraph state, instrument_graph, main_graph
│   ├── api/                # FastAPI + SSE routes (cycles, signals, instruments, news, auth)
│   └── utils/              # logging, time, errors
├── web/                    # React + Vite + TS + Tailwind dashboard
├── scripts/
│   ├── start_api.py        # API only
│   └── run_jarvis.py       # API + APScheduler
├── tests/                  # unit + integration (fixtures in tests/fixtures)
└── data/                   # SQLite (jarvis.db), MT5 parquet cache, fixtures
```

---

## Key principles

1. **Deterministic first** — indicators, structure, SL/TP math, scoring = pure Python; LLM only for news interpretation & rationale
2. **Read-only** — no `order_send`, `order_check`, or trade execution code anywhere (enforced by test)
3. **Typed contracts** — every node reads/writes Pydantic models in shared LangGraph state
4. **Config-driven** — instruments, strategies, weights, thresholds live in YAML
5. **Cache everything** — candles & news cached; agents never re-fetch within a cycle

---

## API highlights

| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/health` | Adapter status (DB, MT5, Anthropic, TimesFM) |
| `POST /api/v1/auth/login` | JWT cookies (HttpOnly) |
| `GET /api/v1/cycles` | Cycle history + status |
| `POST /api/v1/cycles/run` | Manual cycle trigger |
| `GET /api/v1/signals` | Filterable signal history |
| `GET /api/v1/instruments` | Configured instruments |
| `GET /api/v1/news` | Cached news + impact |
| `GET /api/v1/stats` | Win-rate, expectancy per strategy/instrument |
| `GET /api/v1/sse/stream` | SSE: `cycle.started`, `cycle.step`, `instrument.updated`, `news.updated`, `heartbeat` |

---

## Testing

```bash
uv run pytest -q                    # unit + integration
uv run pytest tests/unit/test_login_lockout.py -v  # login rate-limit test
uv run ruff check .                 # lint
uv run mypy src/                    # type check
```

---

## Notes & caveats

- **MT5 is Windows-only**; on macOS/Linux you need a bridge (Wine, remote MT5, or a separate Windows host).
- **TimesFM** runs on CPU (torch); first load downloads weights (~1 GB).
- **News** uses ForexLive RSS by default; `config/news_sources.yaml` can override.
- **Cycle interval** is 900 s (15 min) by default; signals expire after `cycle_interval × 4`.
- **Dashboard** is intentionally chart-free — signals are the product; use your charting platform for execution.

---

## License

Proprietary — internal use only.