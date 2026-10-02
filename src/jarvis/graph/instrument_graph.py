from collections.abc import Callable, Sequence
from typing import Any

from langchain_core.runnables.config import RunnableConfig
from langgraph.graph import END, START, StateGraph

from jarvis.agents.strange import run_strange
from jarvis.agents.war_machine import run_war_machine
from jarvis.config.models import (
    DoctorStrangeSettings,
    InstrumentConfig,
    JarvisConfig,
    RiskSettings,
    SessionWindow,
    StrategiesConfig,
)
from jarvis.graph.state import SymbolState
from jarvis.schemas import SymbolInfo, Tick
from jarvis.strategies.base import BaseStrategy
from jarvis.strategies.context import StrategyContext
from jarvis.strategies.registry import StrategyRegistry


def build_instrument_subgraph(
    instrument: InstrumentConfig,
    strategies_config: StrategiesConfig,
    jarvis_config: JarvisConfig,
    doctor_settings: DoctorStrangeSettings,
    risk_settings: RiskSettings,
    session_windows: Sequence[SessionWindow],
    registry: StrategyRegistry,
) -> StateGraph[SymbolState]:
    """Build a StateGraph for processing a single instrument's lifecycle."""
    
    # Identify which strategies to run based on global enabled flags and instrument profile
    active_strategies = list(registry.create_enabled(strategies_config).values())

    def doctor_strange_node(state: SymbolState) -> dict[str, Any]:
        if "candles" not in state or not state["candles"]:
            raise ValueError("No candles provided to subgraph")
        
        latest_ts = None
        for tf_candles in state["candles"].values():
            if tf_candles:
                tf_latest = tf_candles[-1].timestamp
                if latest_ts is None or tf_latest > latest_ts:
                    latest_ts = tf_latest
        
        if latest_ts is None:
            raise ValueError("Empty candles lists")

        ms = run_strange(
            instrument=instrument,
            candles_by_timeframe=state["candles"],
            settings=doctor_settings,
            session_windows=session_windows,
            now=latest_ts,
        )
        return {"market_structure": ms}

    builder = StateGraph(SymbolState)
    builder.add_node("doctor_strange", doctor_strange_node)

    def merge_node(state: SymbolState) -> dict[str, Any]:
        return {}
    builder.add_node("merge_strategies", merge_node)

    strategy_nodes = []
    for strategy in active_strategies:
        node_name = f"strategy_{strategy.name}"
        strategy_nodes.append(node_name)

        def make_node(strat: BaseStrategy = strategy) -> Callable[[SymbolState], dict[str, Any]]:
            def node(state: SymbolState) -> dict[str, Any]:
                latest_ts = max(
                    c[-1].timestamp for c in state["candles"].values() if c
                )
                if state.get("market_structure") is None:
                    raise ValueError("Market structure is missing")
                
                ctx = StrategyContext(
                    symbol=state["symbol"],
                    candles=state["candles"],
                    market_structure=state["market_structure"], # type: ignore
                    now=latest_ts,
                )
                candidates = strat.analyse(ctx)
                return {"candidates": candidates}
            return node
        
        builder.add_node(node_name, make_node())
        builder.add_edge("doctor_strange", node_name)
        builder.add_edge(node_name, "merge_strategies")

    def war_machine_node(state: SymbolState, config: RunnableConfig) -> dict[str, Any]:
        candidates = state.get("candidates", [])
        if not candidates:
            return {"risk_assessments": {}}
        
        tick: Tick = config["configurable"]["tick"]
        symbol_info: SymbolInfo = config["configurable"]["symbol_info"]
        account_equity: float = config["configurable"]["account_equity"]
        
        ms = state.get("market_structure")
        if ms is None:
            raise ValueError("Market structure is missing")

        assessments = {}
        for candidate in candidates:
            atr_val = ms.atr.get(doctor_settings.primary_timeframe, 1.0)
            mult = instrument.atr_multipliers.get(candidate.strategy, 1.0)
            
            assessment = run_war_machine(
                candidate=candidate,
                tick=tick,
                symbol_info=symbol_info,
                atr_value=atr_val * mult,
                account_equity=account_equity,
                jarvis_config=jarvis_config,
                risk_settings=risk_settings,
            )
            assessments[assessment.candidate_id] = assessment
            
        return {"risk_assessments": assessments}

    builder.add_node("war_machine", war_machine_node)
    builder.add_edge("merge_strategies", "war_machine")
    
    if not strategy_nodes:
        builder.add_edge("doctor_strange", "merge_strategies")

    builder.add_edge(START, "doctor_strange")
    builder.add_edge("war_machine", END)
    
    return builder
