import pytest
from sqlalchemy import text as astext
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session

from jarvis.db.models import CycleModel, InstrumentModel, SignalModel
from jarvis.db.session import init_db, make_engine


@pytest.fixture
def test_db():
    engine = make_engine(":memory:")
    init_db(engine)
    with Session(engine) as session:
        # Pre-populate required FK data
        cycle = CycleModel(id="test_cycle", trigger="MANUAL", status="COMPLETED", config_hash="xxx")
        session.add(cycle)
        instr = InstrumentModel(symbol="XAUUSD", broker_symbol="XAUUSD", agent_name="gold")
        session.add(instr)
        session.commit()
        yield session

def test_signal_confidence_check(test_db):
    # Valid confidence
    sig1 = SignalModel(
        id="sig1", cycle_id="test_cycle", symbol="XAUUSD", decision="NO_TRADE",
        no_trade_reason="test", rationale="test", status="SKIPPED",
        confidence=1.0, score=1.5
    )
    test_db.add(sig1)
    test_db.commit()

    # Invalid confidence
    sig2 = SignalModel(
        id="sig2", cycle_id="test_cycle", symbol="XAUUSD", decision="NO_TRADE",
        no_trade_reason="test", rationale="test", status="SKIPPED",
        confidence=1.5, score=2.0
    )
    test_db.add(sig2)
    with pytest.raises(IntegrityError):
        test_db.commit()

def test_signal_price_ordering_check(test_db):
    # Valid BUY
    sig1 = SignalModel(
        id="sig_buy", cycle_id="test_cycle", symbol="XAUUSD", decision="TRADE",
        direction="BUY", entry=100.0, sl=90.0, tp=110.0,
        rationale="test", status="OPEN", confidence=0.8, score=0.8
    )
    test_db.add(sig1)
    test_db.commit()

    # Invalid BUY (SL > Entry)
    sig2 = SignalModel(
        id="sig_buy_inv", cycle_id="test_cycle", symbol="XAUUSD", decision="TRADE",
        direction="BUY", entry=100.0, sl=110.0, tp=120.0,
        rationale="test", status="OPEN", confidence=0.8, score=0.8
    )
    test_db.add(sig2)
    with pytest.raises(IntegrityError):
        test_db.commit()
    test_db.rollback()

    # Invalid SELL (SL < Entry)
    sig3 = SignalModel(
        id="sig_sell_inv", cycle_id="test_cycle", symbol="XAUUSD", decision="TRADE",
        direction="SELL", entry=100.0, sl=90.0, tp=80.0,
        rationale="test", status="OPEN", confidence=0.8, score=0.8
    )
    test_db.add(sig3)
    with pytest.raises(IntegrityError):
        test_db.commit()
    test_db.rollback()

def test_signal_no_trade_reason_required(test_db):
    # NO_TRADE without reason should fail
    sig1 = SignalModel(
        id="sig_notrade", cycle_id="test_cycle", symbol="XAUUSD", decision="NO_TRADE",
        rationale="test", status="SKIPPED", confidence=0.5, score=0.5
        # missing no_trade_reason
    )
    test_db.add(sig1)
    with pytest.raises(IntegrityError):
        test_db.commit()
    test_db.rollback()

def test_signal_unique_open_per_symbol_direction(test_db):
    # First OPEN BUY
    sig1 = SignalModel(
        id="sig_open1", cycle_id="test_cycle", symbol="XAUUSD", decision="TRADE",
        direction="BUY", entry=100.0, sl=90.0, tp=110.0,
        rationale="test", status="OPEN", confidence=0.5, score=0.5
    )
    test_db.add(sig1)
    test_db.commit()

    # Second OPEN BUY for same symbol should fail
    sig2 = SignalModel(
        id="sig_open2", cycle_id="test_cycle", symbol="XAUUSD", decision="TRADE",
        direction="BUY", entry=105.0, sl=95.0, tp=115.0,
        rationale="test2", status="OPEN", confidence=0.6, score=0.6
    )
    test_db.add(sig2)
    with pytest.raises(IntegrityError):
        test_db.commit()
    test_db.rollback()

    # But OPEN SELL is allowed
    sig3 = SignalModel(
        id="sig_open3", cycle_id="test_cycle", symbol="XAUUSD", decision="TRADE",
        direction="SELL", entry=100.0, sl=110.0, tp=90.0,
        rationale="test3", status="OPEN", confidence=0.7, score=0.7
    )
    test_db.add(sig3)
    test_db.commit()

    # And CLOSED BUY is allowed
    sig1.status = "TP_HIT"
    test_db.commit()
    
    sig4 = SignalModel(
        id="sig_open4", cycle_id="test_cycle", symbol="XAUUSD", decision="TRADE",
        direction="BUY", entry=105.0, sl=95.0, tp=115.0,
        rationale="test4", status="OPEN", confidence=0.6, score=0.6
    )
    test_db.add(sig4)
    test_db.commit()

def test_db_pragmas(test_db):
    # Verify WAL and foreign_keys
    test_db.execute(astext("PRAGMA journal_mode")).scalar()
    # Memory DB defaults to memory journal mode, so we test foreign_keys
    fk = test_db.execute(astext("PRAGMA foreign_keys")).scalar()
    assert fk == 1
