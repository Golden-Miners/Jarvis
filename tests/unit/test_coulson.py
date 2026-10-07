"""Tests for the Coulson outcome tracker agent (T6.1 / J-061)."""
from datetime import UTC, datetime, timedelta

import pytest

from jarvis.agents.coulson import run_coulson
from jarvis.config.models import InstrumentConfig
from jarvis.db.store import SignalStore
from jarvis.graph.state import JarvisState
from jarvis.schemas import Candle, Signal

NOW = datetime(2026, 10, 3, 12, 0, tzinfo=UTC)
TF = "M15"


def make_candle(
    t: datetime, o: float, h: float, low: float, close: float
) -> Candle:
    """Build one M15 candle."""
    return Candle(timestamp=t, open=o, high=h, low=low, close=close, volume=100.0)


def make_signal(
    signal_id: str = "sig-1",
    direction: str = "BUY",
    entry: float = 100.0,
    sl: float = 98.0,
    tp: float = 104.0,
    created_at: datetime = NOW - timedelta(minutes=30),
    expires_at: datetime = NOW + timedelta(minutes=60),
) -> Signal:
    """Build a Signal with explicit direction/levels."""
    return Signal(
        id=signal_id,
        symbol="XAUUSD",
        decision="TRADE",
        direction=direction,  # type: ignore[arg-type]
        entry=entry,
        sl=sl,
        tp=tp,
        rr=2.0,
        score=0.9,
        confidence=0.9,
        score_breakdown={"strategies": 0.9},
        agent_verdicts={"hawkeye": "aligned"},
        rationale="test",
        status="OPEN",
        created_at=created_at,
        expires_at=expires_at,
    )


@pytest.fixture()
def store(tmp_path) -> SignalStore:
    instruments = [
        InstrumentConfig(
            symbol="XAUUSD",
            broker_symbol="XAUUSD.m",
            agent="Iron Man",
            sessions=[],
            atr_multipliers={},
        )
    ]
    return SignalStore(db_path=tmp_path / "jarvis.db", instruments=instruments)


def make_state(signals: list[Signal], candles_by_symbol: dict[str, list[Candle]]) -> JarvisState:
    """Build a JarvisState post-Jarvis with per-symbol M15 candles."""
    state: JarvisState = {
        "cycle_id": "c-coulson",
        "now": NOW,
        "news": [],
        "symbols": {},
        "signals": signals,
        "errors": [],
        "outcomes": [],
    }
    for sym, candles in candles_by_symbol.items():
        state["symbols"] = {
            sym: {
                "symbol": sym,
                "candles": {TF: candles},
                "candidates": [],
                "risk_assessments": {},
            }
        }
    return state


def test_persists_signals_and_completes_cycle(store: SignalStore) -> None:
    state = make_state([make_signal()], {"XAUUSD": []})
    out = run_coulson(state, store, TF, config_hash="h1")
    assert store.get_signal("sig-1") is not None
    cycle = store.get_cycle("c-coulson")
    assert cycle is not None
    assert cycle.status == "COMPLETED"
    assert out.get("outcomes") == []


def test_buy_tp_hit_from_later_candles(store: SignalStore) -> None:
    candles = [
        make_candle(NOW - timedelta(minutes=15), 100.0, 101.0, 99.5, 100.5),
        make_candle(NOW, 100.5, 104.5, 100.0, 104.0),  # high >= tp
    ]
    state = make_state([], {"XAUUSD": candles})
    store.start_cycle("c-coulson", trigger="MANUAL", config_hash="h1")
    store.upsert_signal(make_signal(), "c-coulson")
    out = run_coulson(state, store, TF, config_hash="h1")
    assert len(out["outcomes"]) == 1
    oc = out["outcomes"][0]
    assert oc.result == "TP_HIT"
    assert oc.signal_id == "sig-1"
    assert oc.r_multiple == pytest.approx(2.0)  # (104-100)/(100-98)
    assert store.get_signal("sig-1").status == "TP_HIT"
    row = store.get_outcome("sig-1")
    assert row is not None and row.result == "TP_HIT"
def test_sell_sl_hit_from_later_candles(store: SignalStore) -> None:
    sig = make_signal(direction="SELL", entry=100.0, sl=102.0, tp=96.0)
    candles = [
        make_candle(NOW - timedelta(minutes=15), 100.0, 100.5, 99.5, 100.0),
        make_candle(NOW, 100.0, 102.5, 99.0, 102.0),  # high >= sl
    ]
    state = make_state([], {"XAUUSD": candles})
    store.start_cycle("c-coulson", trigger="MANUAL", config_hash="h1")
    store.upsert_signal(sig, "c-coulson")
    out = run_coulson(state, store, TF, config_hash="h1")
    oc = out["outcomes"][0]
    assert oc.result == "SL_HIT"
    assert oc.r_multiple == pytest.approx(-1.0)  # (100-102)/(102-100)
    assert store.get_signal("sig-1").status == "SL_HIT"


def test_expiry_without_touches_resolves_expired(store: SignalStore) -> None:
    sig = make_signal(expires_at=NOW - timedelta(minutes=1))
    candles = [
        make_candle(NOW - timedelta(minutes=15), 100.0, 101.0, 99.5, 100.5),
        make_candle(NOW, 100.5, 101.5, 100.0, 101.0),  # no SL/TP touch
    ]
    state = make_state([], {"XAUUSD": candles})
    store.start_cycle("c-coulson", trigger="MANUAL", config_hash="h1")
    store.upsert_signal(sig, "c-coulson")
    out = run_coulson(state, store, TF, config_hash="h1")
    oc = out["outcomes"][0]
    assert oc.result == "EXPIRED"
    # r from last close: (101-100)/(100-98) = 0.5
    assert oc.r_multiple == pytest.approx(0.5)
    assert store.get_signal("sig-1").status == "EXPIRED"


def test_same_candle_sl_and_tp_resolves_sl_first(store: SignalStore) -> None:
    """Conservative rule: if a candle touches both, SL is assumed first."""
    sig = make_signal(entry=100.0, sl=99.0, tp=101.0)
    candles = [make_candle(NOW, 100.0, 101.5, 98.5, 100.0)]  # spans both sl and tp
    state = make_state([], {"XAUUSD": candles})
    store.start_cycle("c-coulson", trigger="MANUAL", config_hash="h1")
    store.upsert_signal(sig, "c-coulson")
    out = run_coulson(state, store, TF, config_hash="h1")
    assert out["outcomes"][0].result == "SL_HIT"


def test_open_signal_remains_open_without_touches(store: SignalStore) -> None:
    candles = [make_candle(NOW, 100.0, 100.5, 99.8, 100.2)]
    state = make_state([], {"XAUUSD": candles})
    store.start_cycle("c-coulson", trigger="MANUAL", config_hash="h1")
    store.upsert_signal(make_signal(), "c-coulson")
    out = run_coulson(state, store, TF, config_hash="h1")
    assert out["outcomes"] == []
    assert store.get_signal("sig-1").status == "OPEN"
    assert store.get_outcome("sig-1") is None


def test_candles_before_creation_ignored(store: SignalStore) -> None:
    """Only candles strictly after created_at count towards the outcome."""
    sig = make_signal(created_at=NOW - timedelta(minutes=15))
    # This candle hits TP but predates the signal.
    candles = [
        make_candle(NOW - timedelta(minutes=30), 100.0, 105.0, 99.0, 100.0),
        make_candle(NOW, 100.0, 100.5, 99.8, 100.2),
    ]
    state = make_state([], {"XAUUSD": candles})
    store.start_cycle("c-coulson", trigger="MANUAL", config_hash="h1")
    store.upsert_signal(sig, "c-coulson")
    out = run_coulson(state, store, TF, config_hash="h1")
    assert out["outcomes"] == []


def test_max_favorable_and_adverse_tracked(store: SignalStore) -> None:
    sig = make_signal(expires_at=NOW - timedelta(minutes=1))
    candles = [
        make_candle(NOW - timedelta(minutes=15), 100.0, 102.0, 99.0, 101.0),
        make_candle(NOW, 101.0, 101.5, 98.5, 101.0),
    ]
    state = make_state([], {"XAUUSD": candles})
    store.start_cycle("c-coulson", trigger="MANUAL", config_hash="h1")
    store.upsert_signal(sig, "c-coulson")
    out = run_coulson(state, store, TF, config_hash="h1")
    oc = out["outcomes"][0]
    assert oc.max_favorable == pytest.approx(2.0)  # max high - entry
    assert oc.max_adverse == pytest.approx(1.5)  # entry - min low (100 - 98.5)
    row = store.get_outcome("sig-1")
    assert row is not None and row.max_favorable == pytest.approx(2.0)


def test_missing_symbol_candles_keeps_signal_open(store: SignalStore) -> None:
    """No candles for the symbol: cannot decide, stay OPEN, no error."""
    state = make_state([], {})
    store.start_cycle("c-coulson", trigger="MANUAL", config_hash="h1")
    store.upsert_signal(make_signal(), "c-coulson")
    out = run_coulson(state, store, TF, config_hash="h1")
    assert out["outcomes"] == []
    assert out.get("errors") in (None, [])
    assert store.get_signal("sig-1").status == "OPEN"


def test_duplicate_open_signal_recorded_as_agent_error(store: SignalStore) -> None:
    """Persisting a second OPEN for (symbol, direction) fails loudly but continues."""
    first = make_signal(signal_id="sig-1")
    second = make_signal(signal_id="sig-2")
    state = make_state([first, second], {"XAUUSD": []})
    out = run_coulson(state, store, TF, config_hash="h1")
    errors = out.get("errors", [])
    assert any(e["agent"] == "Coulson" and "sig-2" in e["error"] for e in errors)
    assert store.get_signal("sig-1") is not None
    assert store.get_signal("sig-2") is None
    cycle = store.get_cycle("c-coulson")
    assert cycle is not None and cycle.status == "DEGRADED"


def test_running_twice_is_idempotent(store: SignalStore) -> None:
    candles = [make_candle(NOW, 100.0, 104.5, 100.0, 104.0)]
    state = make_state([], {"XAUUSD": candles})
    store.start_cycle("c-coulson", trigger="MANUAL", config_hash="h1")
    store.upsert_signal(make_signal(), "c-coulson")
    run_coulson(state, store, TF, config_hash="h1")
    out2 = run_coulson(state, store, TF, config_hash="h1")
    # Already resolved: no second outcome, no crash.
    assert out2["outcomes"] == []
    assert store.get_signal("sig-1").status == "TP_HIT"
