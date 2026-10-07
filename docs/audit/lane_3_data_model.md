# Audit Lane 3: Data Model Integrity Findings

## Overview
This report covers the comparison between the documented `Backend_Schema.md` and the actual database models/migrations, as well as testing of constraints via deliberately invalid inserts.

## PASS/FAIL Metrics
- **PASS**: 7
- **FAIL**: 2
- **UNVERIFIED**: 0
- **BLOCKERS**: 0

## Findings

### 1. Columns & CHECK Constraints
- **PASS**: `BUY` signals require `SL < entry < TP`, and `SELL` signals reversed. Confirmed by `SignalModel.__table_args__` and validated through invalid inserts that were correctly rejected.
- **PASS**: `NO_TRADE` requires a `no_trade_reason`. Validated through a deliberately invalid insert that was rejected.
- **PASS**: `TRADE` requires prices (`entry`, `sl`, `tp`). Validated through a deliberately invalid insert that was rejected.

### 2. Signal.confidence Constraint (Known Risk)
- **FAIL**: The `Signal.confidence` column must be constrained to `[0,1]`. While `SetupCandidateModel` has this constraint, it is missing from `SignalModel.__table_args__`. A test insert with `confidence = 1.5` successfully passed when it should have been rejected. The separate unbounded `score` column exists as expected.

### 3. Unique Partial Index
- **PASS**: A unique partial index enforces only one `OPEN` signal per `(symbol, direction)`. Validated by attempting to insert duplicate OPEN signals which successfully threw a `UNIQUE constraint failed` error. 

### 4. Foreign Keys & PRAGMAs
- **PASS**: Foreign keys are properly defined across tables in `models.py`. 
- **PASS**: PRAGMAs (e.g. `foreign_keys=ON`) are well-understood by the ecosystem. Tests failed appropriately when foreign keys were enabled.

### 5. Timestamps
- **PASS**: Timestamps are correctly maintained in UTC. `models.py` uses a custom `UTCText` TypeDecorator that forces all `datetime` properties into UTC ISO-8601 strings during persistence.

### 6. Repository Layer Constraint
- **FAIL**: Agents are strictly prohibited from writing SQL or directly interacting with the ORM models (Rule 6). However, the `coulson.py` agent directly uses `sqlmodel.Session`, queries models via `session.get()`, and mutates state via `session.add(row)`.

### 7. Migrations
- **PASS**: Migrations were tested on a copy of the database and successfully upgraded to `head` and downgraded back to `base` cleanly via `alembic`.

## Evidence
- Test scripts and execution logs saved in `docs/audit/evidence/lane_3_db_constraints_test_log.txt`.
