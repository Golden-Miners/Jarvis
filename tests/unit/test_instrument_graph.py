"""Tests for the instrument subgraph (T4.2)."""

from datetime import UTC, datetime, timedelta
from typing import Any

from langgraph.graph import StateGraph
from langchain_core.runnables.config import RunnableConfig

from jarvis.config.models import (
    DoctorStrangeSettings,
    InstrumentConfig,
    JarvisConfig,
    RiskSettings,
    StrategiesConfig,
    StrategyConfig,
)
from jarvis.graph.instrument_graph import build_instrument_subgraph
from jarvis.graph.state import SymbolState
from jarvis.schemas import Candle, SymbolInfo, Tick
from jarvis.strategies import default_strategy_registry


def test_build_instrument_subgraph() -> None:
    instrument = InstrumentConfig(
        symbol="XAUUSD", broker_symbol="XAUUSD", agent="iron_man", sessions=[], atr_multipliers={}
    )
    strategies_config = StrategiesConfig(strategies=[StrategyConfig(name="hawkeye", weight=1.0, enabled=True, params={})])
    jarvis_config = JarvisConfig(
        risk_percent=1.0, minimum_rr=1.5, min_score=70.0, min_agreeing_strategies=1, cycle_interval_seconds=900
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
        maximum_spread_points=10.0,
    )
    registry = default_strategy_registry()

    graph = build_instrument_subgraph(
        instrument=instrument,
        strategies_config=strategies_config,
        jarvis_config=jarvis_config,
        doctor_settings=doctor_settings,
        risk_settings=risk_settings,
        session_windows=[],
        registry=registry,
    )
    
    assert isinstance(graph, StateGraph)
    compiled = graph.compile()
    
    # We can invoke it with a minimal state
    now = datetime(2025, 1, 1, 12, 0, tzinfo=UTC)

    candles = {
        "M15": [
            Candle(
                timestamp=now - timedelta(minutes=15 * (200 - i)),
                open=100.0, high=101.0, low=99.0, close=100.5, volume=100
            )
            for i in range(200)
        ]
    }
    
    state: SymbolState = {
        "symbol": "XAUUSD",
        "candles": candles,
    }
    
    config: RunnableConfig = {
        "configurable": {
            "tick": Tick(symbol="XAUUSD", bid=100.0, ask=100.1, timestamp=now, volume=1),
            "symbol_info": SymbolInfo(symbol="XAUUSD", digits=2, point=0.01, trade_tick_size=0.01, trade_tick_value=1.0, volume_min=0.01, volume_max=100.0, volume_step=0.01),
            "account_equity": 10000.0,
        }
    }
    
    result = compiled.invoke(state, config=config)
    assert "market_structure" in result
    assert "candidates" in result
    assert "risk_assessments" in result
