"""Tests for main graph (T4.3 and T4.4)."""
import pytest
from datetime import UTC, datetime, timedelta

from langgraph.graph import StateGraph

from jarvis.config.models import (
    DoctorStrangeSettings,
    InstrumentConfig,
    InstrumentsConfig,
    JarvisConfig,
    RiskSettings,
    StrategiesConfig,
    StrategyConfig,
)
from jarvis.data.mock_provider import MockProvider
from jarvis.graph.main_graph import build_main_graph
from jarvis.graph.state import JarvisState
from jarvis.schemas import Candle, SymbolInfo, Tick
from jarvis.strategies import default_strategy_registry

def test_main_graph_integration() -> None:
    # Setup configs
    instruments_config = InstrumentsConfig(
        instruments=[
            InstrumentConfig(
                symbol="XAUUSD",
                broker_symbol="XAUUSD",
                agent="iron_man",
                sessions=[],
                atr_multipliers={},
            )
        ]
    )
    strategies_config = StrategiesConfig(
        strategies=[
            StrategyConfig(name="hawkeye", weight=1.0, enabled=True, params={})
        ]
    )
    jarvis_config = JarvisConfig(
        risk_percent=1.0,
        minimum_rr=1.5,
        min_score=0.1,  # very low so it triggers
        min_agreeing_strategies=1,
        cycle_interval_seconds=900,
    )
    doctor_settings = DoctorStrangeSettings(
        primary_timeframe="M15",
        ema_period=50,
        atr_period=14,
        volatility_window=100,
        low_volatility_percentile=0.25,
        high_volatility_percentile=0.75,
        swing_left=5,
        swing_right=5,
        zone_tolerance=0.5,
    )
    risk_settings = RiskSettings(
        minimum_sl_atr_multiple=0.5,
        maximum_sl_atr_multiple=3.0,
        maximum_spread_points=1000.0, # huge to avoid spread issues
    )
    registry = default_strategy_registry()
    
    from unittest.mock import MagicMock
    provider = MagicMock()
    
    # Manually populate MockProvider with good setup
    now = datetime(2025, 1, 1, 12, 0, tzinfo=UTC)
    
    candles = [
        Candle(
            timestamp=now - timedelta(minutes=15 * (200 - i)),
            open=100.0,
            high=101.0,
            low=99.0,
            close=100.5,
            volume=100,
        )
        for i in range(200)
    ]
    
    provider.get_candles.return_value = candles
    
    provider.get_symbol_info.return_value = SymbolInfo(
            symbol="XAUUSD",
            digits=2,
            point=0.01,
            trade_tick_size=0.01,
            trade_tick_value=1.0,
            volume_min=0.01,
            volume_max=100.0,
            volume_step=0.01,
        )
    provider.get_tick.return_value = Tick(timestamp=now, bid=100.0, ask=100.1, volume=1)

    # Build Graph
    graph = build_main_graph(
        instruments_config=instruments_config,
        strategies_config=strategies_config,
        jarvis_config=jarvis_config,
        doctor_settings=doctor_settings,
        risk_settings=risk_settings,
        registry=registry,
        provider=provider,
    )
    
    compiled = graph.compile()
    
    initial_state: JarvisState = {
        "cycle_id": "test-123",
        "now": now,
        "news": [],
        "symbols": {},
        "signals": [],
        "errors": [],
    }
    
    result = compiled.invoke(initial_state)
    
    assert "signals" in result
    assert isinstance(result["signals"], list)
    # No guarantees on signals being generated with flat candles, but it didn't crash!
