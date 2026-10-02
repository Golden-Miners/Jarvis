# Backend & Schema — JARVIS

Goal: clean, typed, relational storage. No free-form blobs where a column belongs. One source of truth: Pydantic models (`src/jarvis/schemas/`) mirrored by SQLModel tables (`src/jarvis/db/models.py`), migrated with Alembic.

## 1. Storage split
| Data | Store | Why |
|------|-------|-----|
| Signals, cycles, agent runs, news, outcomes, audit | SQLite (WAL mode) `data/jarvis.db` | Relational, queryable, zero-ops |
| Candles (OHLCV) | Parquet `data/candles/{symbol}/{tf}.parquet` | Columnar, fast, append by bar |
| TimesFM weights/cache | `data/models/` | Large binary, never in git |
| Config | YAML in `config/` (snapshotted into DB per cycle) | Reproducibility |
| Secrets | `.env` only | Never in DB/git |
Upgrade path: swap SQLite for PostgreSQL by changing `DATABASE_URL` (SQLModel/Alembic stay unchanged). Don't use SQLite-only tricks.

## 2. Global conventions
- Tables snake_case plural; PK `id` TEXT (ULID/UUID7, sortable); FKs `<table>_id`.
- Timestamps: UTC, ISO-8601 TEXT (`created_at`, `updated_at`); never local time.
- Prices: REAL rounded to the symbol's `digits` before insert; `symbol` always the **canonical** name (e.g. `XAUUSD`); broker symbol lives only in config/`instruments` table.
- Enums enforced with `CHECK` constraints and Pydantic `Literal`.
- Every table has `created_at`; mutable tables also `updated_at`. No hard deletes on signals/outcomes/audit (append-only or soft status).
- JSON columns allowed ONLY for: `evidence` (list[str]) and `payload` in `audit_log`/`news_items.raw`. Everything queryable is a real column.
- `PRAGMA foreign_keys=ON; journal_mode=WAL; busy_timeout=5000` on every connection.
- Validation order: Pydantic → DB constraint. Reject, never "fix silently".

## 3. Tables (DDL)
```sql
CREATE TABLE instruments (
  symbol TEXT PRIMARY KEY,                 -- canonical: XAUUSD
  broker_symbol TEXT NOT NULL,             -- e.g. XAUUSD.m
  agent_name TEXT NOT NULL,                -- Iron Man
  digits INTEGER NOT NULL, point REAL NOT NULL,
  enabled INTEGER NOT NULL DEFAULT 1 CHECK (enabled IN (0,1)),
  created_at TEXT NOT NULL
);

CREATE TABLE cycles (
  id TEXT PRIMARY KEY,
  trigger TEXT NOT NULL CHECK (trigger IN ('SCHEDULED','MANUAL')),
  status TEXT NOT NULL CHECK (status IN ('RUNNING','COMPLETED','DEGRADED','FAILED')),
  config_hash TEXT NOT NULL,               -- links to config_snapshots
  started_at TEXT NOT NULL, finished_at TEXT,
  duration_ms INTEGER
);

CREATE TABLE config_snapshots (
  hash TEXT PRIMARY KEY, yaml_text TEXT NOT NULL, created_at TEXT NOT NULL
);

CREATE TABLE agent_runs (
  id TEXT PRIMARY KEY,
  cycle_id TEXT NOT NULL REFERENCES cycles(id),
  agent TEXT NOT NULL,                     -- 'Hawkeye'
  symbol TEXT REFERENCES instruments(symbol),   -- NULL for global agents
  status TEXT NOT NULL CHECK (status IN ('OK','DEGRADED','ERROR','SKIPPED')),
  error_code TEXT, error_message TEXT,
  latency_ms INTEGER, llm_tokens_in INTEGER, llm_tokens_out INTEGER,
  created_at TEXT NOT NULL
);
CREATE INDEX ix_agent_runs_cycle ON agent_runs(cycle_id);

CREATE TABLE market_structure (
  id TEXT PRIMARY KEY, cycle_id TEXT NOT NULL REFERENCES cycles(id),
  symbol TEXT NOT NULL REFERENCES instruments(symbol),
  trend_m15 TEXT, trend_h1 TEXT, trend_h4 TEXT, trend_d1 TEXT
    CHECK (1=1), -- each validated in Pydantic: UP|DOWN|RANGE
  atr_m15 REAL, atr_h1 REAL, volatility_regime TEXT CHECK (volatility_regime IN ('LOW','NORMAL','HIGH')),
  session TEXT NOT NULL, last_bos_direction TEXT, last_choch_direction TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE key_levels (
  id TEXT PRIMARY KEY, structure_id TEXT NOT NULL REFERENCES market_structure(id),
  price REAL NOT NULL, kind TEXT NOT NULL CHECK (kind IN ('SUPPORT','RESISTANCE','SUPPLY','DEMAND','LIQUIDITY'))
);

CREATE TABLE forecasts (
  id TEXT PRIMARY KEY, cycle_id TEXT NOT NULL REFERENCES cycles(id),
  symbol TEXT NOT NULL REFERENCES instruments(symbol),
  timeframe TEXT NOT NULL, horizon_bars INTEGER NOT NULL,
  expected_direction TEXT NOT NULL CHECK (expected_direction IN ('UP','DOWN','FLAT')),
  strength REAL NOT NULL CHECK (strength BETWEEN 0 AND 1),
  median_end REAL NOT NULL, q10_end REAL NOT NULL, q90_end REAL NOT NULL,
  model_version TEXT NOT NULL, created_at TEXT NOT NULL
);

CREATE TABLE news_items (
  id TEXT PRIMARY KEY, source TEXT NOT NULL, url TEXT NOT NULL,
  url_hash TEXT NOT NULL UNIQUE,           -- dedupe
  title TEXT NOT NULL, published_at TEXT NOT NULL, fetched_at TEXT NOT NULL,
  raw TEXT                                  -- original payload (JSON), debug only
);

CREATE TABLE news_impacts (
  id TEXT PRIMARY KEY, news_item_id TEXT REFERENCES news_items(id),
  cycle_id TEXT NOT NULL REFERENCES cycles(id),
  symbol TEXT NOT NULL REFERENCES instruments(symbol),
  bias TEXT NOT NULL CHECK (bias IN ('BULLISH','BEARISH','NEUTRAL')),
  impact INTEGER NOT NULL CHECK (impact BETWEEN 0 AND 10),
  summary TEXT NOT NULL, model TEXT NOT NULL, created_at TEXT NOT NULL
);

CREATE TABLE calendar_events (
  id TEXT PRIMARY KEY, name TEXT NOT NULL, currency TEXT NOT NULL,
  importance TEXT NOT NULL CHECK (importance IN ('LOW','MEDIUM','HIGH')),
  event_time TEXT NOT NULL, blackout_start TEXT, blackout_end TEXT,
  UNIQUE(name, event_time)
);

CREATE TABLE setup_candidates (
  id TEXT PRIMARY KEY, cycle_id TEXT NOT NULL REFERENCES cycles(id),
  symbol TEXT NOT NULL REFERENCES instruments(symbol),
  strategy TEXT NOT NULL, agent TEXT NOT NULL,
  direction TEXT NOT NULL CHECK (direction IN ('BUY','SELL')),
  entry REAL NOT NULL, sl REAL NOT NULL, tp REAL NOT NULL,
  confidence REAL NOT NULL CHECK (confidence BETWEEN 0 AND 1),
  evidence TEXT NOT NULL,                  -- JSON list[str]
  created_at TEXT NOT NULL
);
CREATE INDEX ix_candidates_cycle_symbol ON setup_candidates(cycle_id, symbol);

CREATE TABLE risk_assessments (
  id TEXT PRIMARY KEY, candidate_id TEXT NOT NULL UNIQUE REFERENCES setup_candidates(id),
  valid INTEGER NOT NULL CHECK (valid IN (0,1)),
  rr REAL NOT NULL, sl_atr_mult REAL NOT NULL, spread_ok INTEGER NOT NULL,
  suggested_lot REAL, issues TEXT NOT NULL DEFAULT '[]', created_at TEXT NOT NULL
);

CREATE TABLE signals (
  id TEXT PRIMARY KEY, cycle_id TEXT NOT NULL REFERENCES cycles(id),
  symbol TEXT NOT NULL REFERENCES instruments(symbol),
  decision TEXT NOT NULL CHECK (decision IN ('TRADE','NO_TRADE')),
  direction TEXT CHECK (direction IN ('BUY','SELL')),
  entry REAL, sl REAL, tp REAL, rr REAL,
  confidence REAL NOT NULL CHECK (confidence BETWEEN 0 AND 1),
  score REAL NOT NULL,
  no_trade_reason TEXT,                    -- required when NO_TRADE (enum code)
  rationale TEXT NOT NULL,
  source_candidate_id TEXT REFERENCES setup_candidates(id),
  status TEXT NOT NULL CHECK (status IN ('OPEN','TP_HIT','SL_HIT','EXPIRED','SKIPPED')),
  created_at TEXT NOT NULL, expires_at TEXT, updated_at TEXT NOT NULL,
  CHECK (decision='NO_TRADE' OR (direction IS NOT NULL AND entry IS NOT NULL AND sl IS NOT NULL AND tp IS NOT NULL)),
  CHECK (decision='TRADE' OR no_trade_reason IS NOT NULL),
  CHECK (direction IS NULL OR (direction='BUY' AND sl<entry AND tp>entry) OR (direction='SELL' AND sl>entry AND tp<entry))
);
CREATE INDEX ix_signals_symbol_created ON signals(symbol, created_at DESC);
CREATE INDEX ix_signals_status ON signals(status);

CREATE TABLE signal_verdicts (             -- per-agent evidence for a signal
  id TEXT PRIMARY KEY, signal_id TEXT NOT NULL REFERENCES signals(id),
  agent TEXT NOT NULL, verdict TEXT NOT NULL CHECK (verdict IN ('BUY','SELL','NEUTRAL','VETO','ERROR')),
  weight REAL NOT NULL, contribution REAL NOT NULL, note TEXT
);

CREATE TABLE outcomes (                    -- hypothetical result tracking (Coulson)
  signal_id TEXT PRIMARY KEY REFERENCES signals(id),
  result TEXT NOT NULL CHECK (result IN ('TP_HIT','SL_HIT','EXPIRED')),
  resolved_at TEXT NOT NULL, r_multiple REAL NOT NULL,
  max_favorable REAL, max_adverse REAL
);

CREATE TABLE users (
  id TEXT PRIMARY KEY, username TEXT NOT NULL UNIQUE, password_hash TEXT NOT NULL,
  role TEXT NOT NULL CHECK (role IN ('OWNER','VIEWER')), active INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL
);

CREATE TABLE audit_log (                   -- append-only
  id TEXT PRIMARY KEY, ts TEXT NOT NULL, actor TEXT NOT NULL,   -- user id or 'system:<agent>'
  action TEXT NOT NULL, entity TEXT, entity_id TEXT, payload TEXT
);
```

## 4. Relationships
```
cycles 1─* agent_runs        cycles 1─* setup_candidates 1─1 risk_assessments
cycles 1─* signals 1─* signal_verdicts      signals 1─0..1 outcomes
instruments 1─* (structure, forecasts, news_impacts, candidates, signals)
news_items 1─* news_impacts
```

## 5. Data integrity rules
1. Signal price sanity enforced by the `CHECK` above (BUY: SL<entry<TP; SELL reversed) AND Pydantic validator.
2. A `TRADE` signal requires a linked, `valid=1` risk assessment (enforced in repository layer).
3. One OPEN signal per `(symbol, direction)` — unique partial index: `CREATE UNIQUE INDEX ux_open_signal ON signals(symbol, direction) WHERE status='OPEN';`
4. Candle validation before persisting: strictly increasing time, no NaN, `high>=max(open,close)`, `low<=min(open,close)`, no gaps beyond session closures; failures mark the symbol `STALE`.
5. Idempotency: re-running the same `cycle_id` upserts, never duplicates (unique keys above).
6. Retention: `agent_runs` 90 days, `news_items` 180 days, signals/outcomes/audit forever; candles keep 5 years per timeframe.

## 6. Repository layer
`src/jarvis/db/`: `session.py`, `models.py`, `repositories/{signals,cycles,news,outcomes}.py`. Agents never write SQL; only repositories do. API returns Pydantic response models (`schemas/api.py`), never ORM objects.

## 7. Migrations & seeding
Alembic: one migration per schema change, reversible, named `NNNN_description.py`. `jarvis db upgrade`, `jarvis db seed` (instruments from YAML). Never edit an applied migration.

## 8. Backup
Nightly `sqlite3 .backup` to `data/backups/jarvis-YYYYMMDD.db`, keep 14; weekly copy off-machine. Test restore monthly.
