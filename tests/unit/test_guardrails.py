"""Tests for JARVIS guardrails — LLM validation, repair, fallback, kill switch."""

from datetime import UTC, datetime

import pytest

from jarvis.guardrails import (
    FuryOutput,
    KillSwitchTrigger,
    NewsClassification,
    RationaleOutput,
    SchemaValidationError,
    check_kill_switch_before_cycle,
    classify_news_keyword,
    get_fallback_rationale,
    get_kill_switch,
    get_kill_switch_status,
    is_kill_switch_tripped,
    keyword_fallback_to_news_impact,
    reset_kill_switch,
    trip_kill_switch,
)
from jarvis.guardrails.fallback import get_detailed_fallback_rationale
from jarvis.guardrails.kill_switch import KillSwitchContext


class TestNewsClassificationSchema:
    """Tests for NewsClassification and FuryOutput schemas."""

    def test_valid_news_classification(self):
        """Valid classification passes validation."""
        nc = NewsClassification(
            symbol="XAUUSD",
            bias="BULLISH",
            impact=8,
            is_high_impact_event=True,
            summary="Fed rate cut expected",
        )
        assert nc.symbol == "XAUUSD"
        assert nc.bias == "BULLISH"
        assert nc.impact == 8
        assert nc.is_high_impact_event is True

    def test_invalid_bias_rejected(self):
        """Invalid bias value is rejected."""
        with pytest.raises(ValueError):
            NewsClassification(
                symbol="XAUUSD",
                bias="INVALID",
                impact=5,
                is_high_impact_event=False,
                summary="test",
            )

    def test_impact_bounds_enforced(self):
        """Impact must be 0-10."""
        with pytest.raises(ValueError):
            NewsClassification(
                symbol="XAUUSD",
                bias="BULLISH",
                impact=15,  # > 10
                is_high_impact_event=False,
                summary="test",
            )
        with pytest.raises(ValueError):
            NewsClassification(
                symbol="XAUUSD",
                bias="BULLISH",
                impact=-1,  # < 0
                is_high_impact_event=False,
                summary="test",
            )

    def test_fury_output_valid(self):
        """Valid FuryOutput passes."""
        fo = FuryOutput(classifications=[
            NewsClassification(
                symbol="XAUUSD",
                bias="BULLISH",
                impact=8,
                is_high_impact_event=True,
                summary="Fed cuts rates",
            )
        ])
        assert len(fo.classifications) == 1


class TestRationaleOutputSchema:
    """Tests for RationaleOutput schema."""

    def test_valid_rationale(self):
        """Valid rationale passes (10-2000 chars)."""
        ro = RationaleOutput(rationale="Trade approved based on strong confluence of factors.")
        assert len(ro.rationale) >= 10
        assert len(ro.rationale) <= 2000

    def test_short_rationale_rejected(self):
        """Rationale < 10 chars rejected."""
        with pytest.raises(ValueError):
            RationaleOutput(rationale="n/a")

    def test_long_rationale_rejected(self):
        """Rationale > 2000 chars rejected."""
        with pytest.raises(ValueError):
            RationaleOutput(rationale="x" * 2001)


class TestKeywordFallback:
    """Tests for deterministic keyword fallback."""

    def test_xauusd_fed_classification(self):
        """XAUUSD FED keyword -> BEARISH high impact."""
        result = classify_news_keyword(
            "Fed announces rate cut",
            "Federal Reserve cuts rates by 25bps",
            ["XAUUSD"],
        )
        assert isinstance(result, FuryOutput)
        assert len(result.classifications) == 1
        c = result.classifications[0]
        assert c.symbol == "XAUUSD"
        assert c.bias == "BEARISH"
        assert c.impact >= 7
        assert c.is_high_impact_event is True

    def test_btcusd_etf_classification(self):
        """BTCUSD ETF keyword -> BULLISH high impact."""
        result = classify_news_keyword(
            "Bitcoin ETF approved",
            "SEC approves spot Bitcoin ETF",
            ["BTCUSD"],
        )
        c = result.classifications[0]
        assert c.symbol == "BTCUSD"
        assert c.bias == "BULLISH"
        assert c.is_high_impact_event is True

    def test_no_match_neutral(self):
        """No keyword match -> NEUTRAL low impact."""
        result = classify_news_keyword(
            "Random unrelated news",
            "Nothing about markets here",
            ["XAUUSD"],
        )
        c = result.classifications[0]
        assert c.bias == "NEUTRAL"
        assert c.impact == 3
        assert c.is_high_impact_event is False

    def test_multiple_symbols(self):
        """Multiple symbols each get classified."""
        result = classify_news_keyword(
            "Fed and ETF news",
            "Fed rate cut and Bitcoin ETF approval",
            ["XAUUSD", "BTCUSD"],
        )
        assert len(result.classifications) == 2
        symbols = {c.symbol for c in result.classifications}
        assert symbols == {"XAUUSD", "BTCUSD"}

    def test_keyword_fallback_to_news_impact(self):
        """Convert FuryOutput to NewsImpact with blackout."""
        now = datetime.now(UTC)
        fury_output = FuryOutput(classifications=[
            NewsClassification(
                symbol="XAUUSD",
                bias="BULLISH",
                impact=8,
                is_high_impact_event=True,
                summary="test",
            ),
            NewsClassification(
                symbol="BTCUSD",
                bias="NEUTRAL",
                impact=3,
                is_high_impact_event=False,
                summary="test",
            ),
        ])

        impacts = keyword_fallback_to_news_impact(fury_output, now, 60)

        assert "XAUUSD" in impacts
        assert "BTCUSD" in impacts
        assert impacts["XAUUSD"][0].bias == "BULLISH"
        assert impacts["XAUUSD"][0].blackout_until is not None
        assert impacts["BTCUSD"][0].blackout_until is None


class TestRationaleFallback:
    """Tests for template rationale fallback."""

    def test_get_fallback_rationale_minimal(self):
        """Minimal fallback rationale is generated."""
        rationale = get_fallback_rationale(
            symbol="XAUUSD",
            direction="BUY",
            score=1.5,
            score_breakdown={"strategies": 1.0, "structure": 0.5},
            agent_verdicts={"hawkeye": "Candidate provided", "doctor_strange": "Aligned"},
        )
        assert "XAUUSD" in rationale
        assert "BUY" in rationale
        assert "1.50" in rationale

    def test_get_detailed_fallback_rationale(self):
        """Detailed fallback rationale includes trade params."""
        rationale = get_detailed_fallback_rationale(
            symbol="XAUUSD",
            direction="BUY",
            score=1.5,
            score_breakdown={"strategies": 1.0},
            agent_verdicts={"hawkeye": "Candidate provided"},
            entry=2000.0,
            sl=1995.0,
            tp=2010.0,
            rr=2.0,
        )
        assert "XAUUSD" in rationale
        assert "BUY" in rationale
        assert "2000" in rationale
        assert "1995" in rationale
        assert "2010" in rationale


class TestKillSwitch:
    """Tests for kill switch functionality."""

    def setup_method(self):
        """Reset kill switch before each test."""
        reset_kill_switch()

    def teardown_method(self):
        """Reset kill switch after each test."""
        reset_kill_switch()

    def test_initial_state_inactive(self):
        """Kill switch starts inactive."""
        assert get_kill_switch() is False
        assert is_kill_switch_tripped() is False
        assert check_kill_switch_before_cycle() is True

    def test_trip_kill_switch(self):
        """Trip kill switch blocks new cycles."""
        trip_kill_switch(KillSwitchTrigger.MANUAL, "Test trigger")
        assert get_kill_switch() is True
        assert is_kill_switch_tripped() is True
        assert check_kill_switch_before_cycle() is False

    def test_kill_switch_status_reports_trigger(self):
        """Kill switch status includes trigger and reason."""
        trip_kill_switch(KillSwitchTrigger.GUARDRAIL_VIOLATION, "LLM validation failed")
        status = get_kill_switch_status()
        assert status.active is True
        assert status.triggered_by == "guardrail_violation"
        assert "LLM validation failed" in (status.reason or "")

    def test_reset_kill_switch(self):
        """Reset clears kill switch."""
        trip_kill_switch(KillSwitchTrigger.MANUAL)
        reset_kill_switch()
        assert get_kill_switch() is False
        assert check_kill_switch_before_cycle() is True

    def test_consecutive_trips_idempotent(self):
        """Multiple trips don't error."""
        trip_kill_switch(KillSwitchTrigger.MANUAL)
        trip_kill_switch(KillSwitchTrigger.CONFIG_THRESHOLD)
        assert get_kill_switch() is True

    def test_kill_switch_context_manager(self):
        """Context manager temporarily trips kill switch."""
        assert get_kill_switch() is False
        with KillSwitchContext(KillSwitchTrigger.MANUAL, "test"):
            assert get_kill_switch() is True
        assert get_kill_switch() is False

    def test_kill_switch_context_manager_nested(self):
        """Nested context managers work correctly."""
        assert get_kill_switch() is False
        with KillSwitchContext(KillSwitchTrigger.MANUAL, "outer"):
            assert get_kill_switch() is True
            with KillSwitchContext(KillSwitchTrigger.GUARDRAIL_VIOLATION, "inner"):
                assert get_kill_switch() is True
            assert get_kill_switch() is True
        assert get_kill_switch() is False


class TestSchemaValidationError:
    """Tests for SchemaValidationError exception."""

    def test_exception_contains_metadata(self):
        """Exception preserves schema name and raw output."""
        exc = SchemaValidationError(
            "Validation failed",
            schema_name="FuryOutput",
            raw_output='{"invalid": true}',
        )
        assert exc.schema_name == "FuryOutput"
        assert exc.raw_output == '{"invalid": true}'
        assert str(exc) == "Validation failed"


class TestGuardrailIntegration:
    """Integration tests for guardrail components."""

    def test_fury_output_to_news_impact_roundtrip(self):
        """Full roundtrip: keyword classify -> NewsImpact -> check fields."""
        now = datetime.now(UTC)
        result = classify_news_keyword(
            "Fed rate decision",
            "FOMC meeting minutes released",
            ["XAUUSD", "XAGUSD"],
        )
        impacts = keyword_fallback_to_news_impact(result, now, 60)

        for sym, news_list in impacts.items():
            for news in news_list:
                assert news.symbol == sym
                assert news.bias in ("BULLISH", "BEARISH", "NEUTRAL")
                assert 0 <= news.impact <= 10
                assert isinstance(news.events, list)
                assert isinstance(news.summary, str)

    def test_rationale_fallback_meets_schema_constraints(self):
        """Fallback rationale satisfies RationaleOutput constraints."""
        rationale = get_fallback_rationale(
            symbol="XAUUSD",
            direction="BUY",
            score=1.5,
            score_breakdown={"strategies": 1.0},
            agent_verdicts={"hawkeye": "ok"},
        )
        # Should pass RationaleOutput validation
        validated = RationaleOutput(rationale=rationale)
        assert 10 <= len(validated.rationale) <= 2000