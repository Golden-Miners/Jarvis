"""Tests for the SQLite signal store (T6.1 / J-060)."""
from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from jarvis.config.models import InstrumentConfig
from jarvis.db import models
from jarvis.db.store import SignalStore
from jarvis.schemas import Outcome, Signal
from jarvis.schemas.models import SignalStatus

NOW = datetime(2026, 10, 3, 12, 0, tzinfo=UTC)


def make_signal(
    symbol: str = "XAUUSD",
    direction: str | None = "BUY",
    entry: float = 100.0,
    sl: float = 98.0,
    tp: float = 104.0,
    status: SignalStatus = "OPEN",
    signal_id: str = "sig-1",
    decision: str = "TRADE",
    use_no_trade: bool = False,
) -> Signal:
    """Build a valid Signal for store tests."""
    if use_no_trade:
        kwargs: dict[str, object] = dict(
            symbol=symbol,
            decision="NO_TRADE",
            direction=None,
            entry=None,
            sl=None,
            tp=None,
            status=status,
            created_at=NOW,
            expires_at=NOW + timedelta(minutes=60),
        )
    else:
        kwargs = dict(
            symbol=symbol,
            decision=decision,
            direction=direction,
            entry=entry,
            sl=sl,
            tp=tp,
            status=status,
            created_at=NOW,
            expires_at=NOW + timedelta(minutes=60),
        )
    sig = Signal(
        id=signal_id,
        score=0.9,
        confidence=0.9,
        score_breakdown={"strategies": 0.9},
        agent_verdicts={"hawkeye": "aligned"},
        rationale="test",
        **kwargs,
    )
    return sig


@pytest.fixture()
def store(tmp_path) -> SignalStore:
    db_path = tmp_path / "data" / "jarvis.db"
    instruments = [
        InstrumentConfig(
            symbol="XAUUSD",
            broker_symbol="XAUUSD.m",
            agent="Iron Man",
            sessions=[],
            atr_multipliers={},
        ),
        InstrumentConfig(
            symbol="BTCUSD",
            broker_symbol="BTCUSD",
            agent="Black Panther",
            sessions=[],
            atr_multipliers={},
        ),
    ]
    return SignalStore(db_path=db_path, instruments=instruments)


def test_pragmas_applied(store: SignalStore) -> None:
    """Backend_Schema §2: foreign_keys ON, WAL, busy_timeout 5000."""
    with store.session() as session:
        fk = session.execute(text("PRAGMA foreign_keys")).scalar_one()
        journal = session.execute(text("PRAGMA journal_mode")).scalar_one()
        busy = session.execute(text("PRAGMA busy_timeout")).scalar_one()
    assert fk == 1
    assert journal == "wal"
    assert busy == 5000


def test_instruments_seeded(store: SignalStore) -> None:
    with store.session() as session:
        rows = session.query(models.InstrumentModel).all()
    symbols = {r.symbol for r in rows}
    assert symbols == {"XAUUSD", "BTCUSD"}
    xau = next(r for r in rows if r.symbol == "XAUUSD")
    assert xau.broker_symbol == "XAUUSD.m"
    assert xau.enabled == 1


def test_cycle_upsert_is_idempotent(store: SignalStore) -> None:
    store.start_cycle("c1", trigger="MANUAL", config_hash="abc", config_text="{}")
    store.start_cycle("c1", trigger="MANUAL", config_hash="abc", config_text="{}")
    cycle = store.get_cycle("c1")
    assert cycle is not None
    assert cycle.status in ("RUNNING", "COMPLETED", "DEGRADED", "FAILED")
    assert cycle.trigger == "MANUAL"
    with store.session() as session:
        assert session.query(models.CycleModel).count() == 1


def test_complete_cycle_sets_status_and_duration(store: SignalStore) -> None:
    store.start_cycle("c1", trigger="MANUAL", config_hash="abc", config_text="{}")
    finished = NOW + timedelta(seconds=42)
    store.complete_cycle("c1", "COMPLETED", finished_at=finished, duration_ms=42000)
    cycle = store.get_cycle("c1")
    assert cycle is not None
    assert cycle.status == "COMPLETED"
    assert cycle.finished_at == finished
    assert cycle.duration_ms == 42000


def test_upsert_signal_inserts_and_updates(store: SignalStore) -> None:
    store.start_cycle("c1", trigger="MANUAL", config_hash="abc", config_text="{}")
    store.upsert_signal(make_signal(), "c1")
    assert store.get_signal("sig-1") is not None
    assert store.get_signal("sig-1").status == "OPEN"
    # Re-upserting the same signal id must not duplicate.
    store.upsert_signal(make_signal(), "c1")
    with store.session() as session:
        assert session.query(models.SignalModel).count() == 1
    # Update path: new signal status reflected.
    store.upsert_signal(make_signal(status="TP_HIT"), "c1")
    assert store.get_signal("sig-1").status == "TP_HIT"


def test_unique_open_signal_index_enforced(store: SignalStore) -> None:
    """J-060: unique OPEN signal per (symbol, direction)."""
    store.start_cycle("c1", trigger="MANUAL", config_hash="abc", config_text="{}")
    store.upsert_signal(make_signal(signal_id="sig-1"), "c1")
    with pytest.raises(IntegrityError):
        store.upsert_signal(make_signal(signal_id="sig-2"), "c1")
    # Same symbol+direction but different status is allowed.
    store.upsert_signal(make_signal(signal_id="sig-3", status="TP_HIT"), "c1")
    # Opposite direction for the same symbol is allowed.
    store.upsert_signal(
        make_signal(signal_id="sig-4", direction="SELL", entry=100.0, sl=102.0, tp=96.0),
        "c1",
    )


def test_no_trade_signals_not_limited_by_open_index(store: SignalStore) -> None:
    store.start_cycle("c1", trigger="MANUAL", config_hash="abc", config_text="{}")
    store.upsert_signal(make_signal(signal_id="n1", use_no_trade=True), "c1")
    store.upsert_signal(make_signal(signal_id="n2", use_no_trade=True), "c1")
    with store.session() as session:
        assert session.query(models.SignalModel).count() == 2


def test_bad_price_sanity_rejected(store: SignalStore) -> None:
    """CHECK: BUY requires sl < entry < tp."""
    store.start_cycle("c1", trigger="MANUAL", config_hash="abc", config_text="{}")
    with pytest.raises((IntegrityError, ValidationError)):
        store.upsert_signal(make_signal(signal_id="bad", sl=101.0, tp=99.0), "c1")
    assert store.get_signal("bad") is None


def test_get_open_signals_filters(store: SignalStore) -> None:
    store.start_cycle("c1", trigger="MANUAL", config_hash="abc", config_text="{}")
    store.upsert_signal(make_signal(signal_id="open-1"), "c1")
    store.upsert_signal(make_signal(signal_id="closed-1", status="SL_HIT"), "c1")
    opens = store.get_open_signals()
    assert {s.id for s in opens} == {"open-1"}
    by_symbol = store.get_open_signals(symbol="XAUUSD")
    assert [s.symbol for s in by_symbol] == ["XAUUSD"]


def test_resolve_outcome_writes_row_and_updates_status(store: SignalStore) -> None:
    store.start_cycle("c1", trigger="MANUAL", config_hash="abc", config_text="{}")
    store.upsert_signal(make_signal(), "c1")
    outcome = Outcome(
        signal_id="sig-1",
        result="TP_HIT",
        resolved_at=NOW + timedelta(minutes=30),
        r_multiple=2.0,
        max_favorable=4.0,
        max_adverse=0.5,
    )
    store.resolve_outcome(outcome)
    assert store.get_signal("sig-1").status == "TP_HIT"
    row = store.get_outcome("sig-1")
    assert row is not None
    assert row.r_multiple == 2.0
    assert row.max_favorable == 4.0
    # One outcome per signal: a second resolve must fail.
    with pytest.raises(IntegrityError):
        store.resolve_outcome(outcome)


def test_outcome_requires_existing_signal(store: SignalStore) -> None:
    outcome = Outcome(
        signal_id="ghost",
        result="EXPIRED",
        resolved_at=NOW,
        r_multiple=0.0,
    )
    with pytest.raises(LookupError):
        store.resolve_outcome(outcome)
