import math
from datetime import UTC, datetime

import pytest

from jarvis.agents.jarvis import run_jarvis
from jarvis.config.models import JarvisConfig
from jarvis.graph.state import SymbolState
from jarvis.schemas import Forecast, MarketStructure, NewsImpact, RiskAssessment, SetupCandidate


@pytest.fixture
def mock_jarvis_config() -> JarvisConfig:
    return JarvisConfig(
        risk_percent=1.0,
        minimum_rr=1.5,
        min_score=1.5,
        min_agreeing_strategies=1,
        cycle_interval_seconds=900,
        w_strategy=1.0,
        w_structure=0.5,
        w_forecast=0.5,
        w_news=0.5,
    )

def test_run_jarvis_approves_trade(mock_jarvis_config: JarvisConfig) -> None:
    now = datetime.now(UTC)
    
    cand = SetupCandidate(
        symbol="XAUUSD",
        strategy="hawkeye",
        agent="iron_man",
        direction="BUY",
        entry=100.0,
        sl=99.0,
        tp=102.0,
        confidence=0.8,
        evidence=[],
        created_at=now
    )
    
    # cid logic inside jarvis:
    cid = (
        f"{cand.symbol}:{cand.strategy}:{cand.created_at.isoformat()}"
        f":{cand.direction}:{cand.entry}:{cand.sl}:{cand.tp}"
    )
    
    state: SymbolState = {
        "symbol": "XAUUSD",
        "candles": {},
        "candidates": [cand],
        "risk_assessments": {
            cid: RiskAssessment(
                candidate_id=cid,
                valid=True,
                rr=2.0,
                sl_atr_mult=1.0,
                spread_ok=True,
                suggested_lot=0.1,
                issues=[]
            )
        },
        "market_structure": MarketStructure(
            symbol="XAUUSD",
            timeframe_trends={"primary": "UP"},
            last_bos=None,
            last_choch=None,
            key_levels=[],
            atr={"primary": 1.0},
            volatility_regime="NORMAL",
            session="NY"
        ),
        "forecast": Forecast(
            symbol="XAUUSD",
            horizon_bars=32,
            timeframe="M15",
            median=[101.0],
            q10=[],
            q90=[],
            expected_direction="UP",
            strength=0.9
        ),
        "_tick": None,
        "_symbol_info": None,
    }
    
    news = [
        NewsImpact(
            symbol="XAUUSD",
            bias="BULLISH",
            impact=8,
            blackout_until=None,
            events=[],
            summary="Good news"
        )
    ]
    
    # Score should be:
    # w_strat * 0.8 = 0.8
    # structure UP + BUY = 0.5
    # forecast UP + BUY = 0.5 * 0.9 = 0.45
    # news BULLISH = 0.5
    # Total = 2.25 >= 1.5 -> APPROVED
    
    signal = run_jarvis(state, news, mock_jarvis_config, llm=None)
    
    assert signal is not None
    assert signal.decision == "TRADE"
    assert signal.direction == "BUY"
    assert signal.score == pytest.approx(2.25)
    assert signal.confidence == pytest.approx(1.0 - math.exp(-2.25))
    # With llm=None, uses template fallback
    assert "XAUUSD" in signal.rationale
    assert "BUY" in signal.rationale
    assert "2.25" in signal.rationale
    assert "template fallback" in signal.rationale.lower()
