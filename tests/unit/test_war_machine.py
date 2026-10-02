from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from jarvis.agents import run_war_machine
from jarvis.config.models import JarvisConfig, RiskSettings
from jarvis.schemas import SetupCandidate, SymbolInfo, Tick

NOW = datetime(2026, 1, 1, tzinfo=UTC)


def _jarvis(**overrides: object) -> JarvisConfig:
    values: dict[str, object] = {
        "min_score": 0,
        "minimum_rr": 1.5,
        "min_agreeing_strategies": 2,
        "risk_percent": 1.0,
        "cycle_interval_seconds": 900,
    }
    values.update(overrides)
    return JarvisConfig(**values)


def _risk_settings(**overrides: object) -> RiskSettings:
    values: dict[str, object] = {
        "minimum_sl_atr_multiple": 0.5,
        "maximum_sl_atr_multiple": 2.0,
        "maximum_spread_points": 20,
    }
    values.update(overrides)
    return RiskSettings(**values)


def _candidate(
    direction: str = "BUY", entry: float = 100, sl: float = 98, tp: float = 104
) -> SetupCandidate:
    return SetupCandidate(
        symbol="XAUUSD",
        strategy="test",
        agent="war_machine",
        direction=direction,  # type: ignore[arg-type]
        entry=entry,
        sl=sl,
        tp=tp,
        confidence=0.8,
        evidence=[],
        created_at=NOW,
    )


def _symbol_info(**overrides: float) -> SymbolInfo:
    values: dict[str, float | int | str] = {
        "symbol": "XAUUSD",
        "digits": 2,
        "point": 0.1,
        "trade_tick_size": 0.1,
        "trade_tick_value": 1.0,
        "volume_min": 0.1,
        "volume_max": 10.0,
        "volume_step": 0.1,
    }
    values.update(overrides)
    return SymbolInfo(**values)  # type: ignore[arg-type]


def _tick(bid: float = 100, ask: float = 100.5) -> Tick:
    return Tick(timestamp=NOW, bid=bid, ask=ask)


def test_valid_buy_candidate_calculates_rr_atr_spread_and_lot() -> None:
    result = run_war_machine(
        _candidate(), _tick(), _symbol_info(), 2, 10_000, _jarvis(), _risk_settings()
    )

    assert result.valid is True
    assert result.rr == 2
    assert result.sl_atr_mult == 1
    assert result.spread_ok is True
    assert result.suggested_lot == 5.0
    assert result.issues == []
    assert result.candidate_id.endswith(":BUY:100.0:98.0:104.0")


def test_candidates_with_same_symbol_strategy_and_time_have_distinct_ids() -> None:
    first = run_war_machine(
        _candidate(), _tick(), _symbol_info(), 2, 10_000, _jarvis(), _risk_settings()
    )
    second = run_war_machine(
        _candidate("BUY", entry=101, sl=99, tp=105),
        _tick(),
        _symbol_info(),
        2,
        10_000,
        _jarvis(),
        _risk_settings(),
    )

    assert first.candidate_id != second.candidate_id


def test_valid_sell_candidate_uses_directional_price_distances() -> None:
    result = run_war_machine(
        _candidate("SELL", entry=100, sl=102, tp=96),
        _tick(),
        _symbol_info(),
        2,
        10_000,
        _jarvis(),
        _risk_settings(),
    )

    assert result.valid is True
    assert result.rr == 2
    assert result.sl_atr_mult == 1
    assert result.suggested_lot == 5.0


def test_lot_rounds_down_to_volume_step_and_caps_at_maximum() -> None:
    rounded = run_war_machine(
        _candidate(), _tick(), _symbol_info(), 2, 10_500, _jarvis(), _risk_settings()
    )
    capped = run_war_machine(
        _candidate(),
        _tick(),
        _symbol_info(),
        2,
        1_000_000,
        _jarvis(),
        _risk_settings(),
    )

    assert rounded.suggested_lot == 5.2
    assert capped.suggested_lot == 10.0


def test_invalid_rr_atr_geometry_and_spread_are_reported() -> None:
    result = run_war_machine(
        _candidate(sl=97, tp=101),
        _tick(bid=100, ask=103),
        _symbol_info(),
        2,
        10_000,
        _jarvis(),
        _risk_settings(maximum_spread_points=20, maximum_sl_atr_multiple=1.0),
    )

    assert result.valid is False
    assert result.rr == pytest.approx(1 / 3)
    assert result.spread_ok is False
    assert "reward:risk below minimum" in result.issues
    assert "stop distance outside ATR bounds" in result.issues
    assert "spread exceeds maximum" in result.issues


def test_invalid_directional_geometry_returns_zero_metrics_and_no_lot() -> None:
    result = run_war_machine(
        _candidate(sl=101, tp=99),
        _tick(),
        _symbol_info(),
        2,
        10_000,
        _jarvis(),
        _risk_settings(),
    )

    assert result.valid is False
    assert result.rr == 0
    assert result.sl_atr_mult == 0
    assert result.suggested_lot is None
    assert "invalid directional price geometry" in result.issues


def test_below_minimum_risk_lot_is_not_rounded_up() -> None:
    result = run_war_machine(
        _candidate(),
        _tick(),
        _symbol_info(volume_min=1.0),
        2,
        100,
        _jarvis(),
        _risk_settings(),
    )

    assert result.valid is False
    assert result.suggested_lot is None
    assert "risk-sized lot is below broker minimum" in result.issues


def test_risk_lot_below_minimum_by_fractional_step_is_not_rounded_up() -> None:
    result = run_war_machine(
        _candidate(),
        _tick(),
        _symbol_info(volume_min=0.1),
        2,
        199,
        _jarvis(),
        _risk_settings(),
    )

    assert result.valid is False
    assert result.suggested_lot is None


def test_invalid_equity_atr_or_symbol_mismatch_is_rejected() -> None:
    with pytest.raises(ValueError, match="atr_value"):
        run_war_machine(
            _candidate(), _tick(), _symbol_info(), 0, 10_000, _jarvis(), _risk_settings()
        )
    with pytest.raises(ValueError, match="account_equity"):
        run_war_machine(
            _candidate(), _tick(), _symbol_info(), 2, 0, _jarvis(), _risk_settings()
        )
    with pytest.raises(ValueError, match="does not match"):
        run_war_machine(
            _candidate(),
            _tick(),
            _symbol_info(symbol="EURUSD"),
            2,
            10_000,
            _jarvis(),
            _risk_settings(),
        )


def test_risk_settings_require_ordered_atr_bounds() -> None:
    with pytest.raises(ValidationError, match="maximum SL ATR multiple"):
        _risk_settings(minimum_sl_atr_multiple=2, maximum_sl_atr_multiple=1)
