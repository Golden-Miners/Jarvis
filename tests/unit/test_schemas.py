from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from jarvis.schemas import (
    Forecast,
    MarketStructure,
    NewsImpact,
    RiskAssessment,
    SetupCandidate,
    Signal,
)

NOW = datetime.now(UTC)


def test_market_structure_accepts_documented_contract() -> None:
    model = MarketStructure(
        symbol="XAUUSD",
        timeframe_trends={"M15": "UP", "H1": "RANGE"},
        key_levels=[2300.0],
        atr={"M15": 12.5},
        volatility_regime="NORMAL",
        session="LONDON",
    )

    assert model.last_bos is None
    assert model.last_choch is None


def test_news_impact_bounds_impact_and_defaults_events() -> None:
    model = NewsImpact(symbol="XAUUSD", bias="NEUTRAL", impact=10)

    assert model.events == []
    with pytest.raises(ValidationError):
        NewsImpact(symbol="XAUUSD", bias="NEUTRAL", impact=11)


def test_forecast_requires_positive_horizon_and_bounded_strength() -> None:
    forecast = Forecast(
        symbol="XAUUSD",
        horizon_bars=32,
        timeframe="M15",
        median=[2301.0],
        q10=[2298.0],
        q90=[2304.0],
        expected_direction="UP",
        strength=0.5,
    )

    assert forecast.horizon_bars == 32
    with pytest.raises(ValidationError):
        Forecast.model_validate({**forecast.model_dump(), "horizon_bars": 0})
    with pytest.raises(ValidationError):
        Forecast.model_validate({**forecast.model_dump(), "strength": 1.1})


def test_setup_candidate_validates_direction_and_confidence() -> None:
    candidate = SetupCandidate(
        symbol="XAUUSD",
        strategy="trend",
        agent="black_widow",
        direction="BUY",
        entry=2300.0,
        sl=2290.0,
        tp=2320.0,
        confidence=0.8,
        evidence=["higher highs"],
        created_at=NOW,
    )

    assert candidate.direction == "BUY"
    with pytest.raises(ValidationError):
        SetupCandidate(
            symbol="XAUUSD",
            strategy="trend",
            agent="black_widow",
            direction="HOLD",
            entry=2300.0,
            sl=2290.0,
            tp=2320.0,
            confidence=0.8,
            evidence=[],
            created_at=NOW,
        )


def test_risk_assessment_accepts_optional_lot() -> None:
    assessment = RiskAssessment(
        candidate_id="candidate-1",
        valid=True,
        rr=2.0,
        sl_atr_mult=1.5,
        spread_ok=True,
        issues=[],
    )

    assert assessment.suggested_lot is None


def test_signal_models_no_trade_without_price_fields() -> None:
    signal = Signal(
        id="signal-1",
        symbol="XAUUSD",
        decision="NO_TRADE",
        confidence=0.2,
        score=0.2,
        score_breakdown={"strategy": 0.2},
        agent_verdicts={"hawkeye": "NO_SETUP"},
        rationale="No aligned setup.",
        status="SKIPPED",
        created_at=NOW,
        expires_at=NOW,
    )

    assert signal.direction is None
    assert signal.entry is None
    with pytest.raises(ValidationError):
        Signal.model_validate({**signal.model_dump(), "decision": "BUY"})
