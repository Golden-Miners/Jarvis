from collections.abc import Callable
from typing import Any

from langgraph.constants import Send
from langgraph.graph import END, START, StateGraph
from langchain_core.runnables.config import RunnableConfig

from jarvis.agents.vision import run_vision
from jarvis.config.models import (
    DoctorStrangeSettings,
    InstrumentsConfig,
    JarvisConfig,
    RiskSettings,
    StrategiesConfig,
)
from jarvis.data.provider import DataProvider
from jarvis.graph.instrument_graph import build_instrument_subgraph
from jarvis.graph.state import JarvisState, SymbolState
from jarvis.graph.wrapper import safe_node
from jarvis.strategies.registry import StrategyRegistry


def build_main_graph(
    instruments_config: InstrumentsConfig,
    strategies_config: StrategiesConfig,
    jarvis_config: JarvisConfig,
    doctor_settings: DoctorStrangeSettings,
    risk_settings: RiskSettings,
    registry: StrategyRegistry,
    provider: DataProvider,
) -> StateGraph[JarvisState]:
    
    subgraphs = {}
    for instrument in instruments_config.instruments:
        subgraph = build_instrument_subgraph(
            instrument=instrument,
            strategies_config=strategies_config,
            jarvis_config=jarvis_config,
            doctor_settings=doctor_settings,
            risk_settings=risk_settings,
            session_windows=[],  # Session windows aren't configured yet
            registry=registry,
        )
        subgraphs[instrument.symbol] = subgraph.compile()

    builder = StateGraph(JarvisState)

    @safe_node("Vision")
    def vision_node(state: JarvisState) -> dict[str, Any]:
        timeframes = [doctor_settings.primary_timeframe, "H1", "H4", "D1"]
        
        res = run_vision(
            provider=provider,
            instruments=instruments_config.instruments,
            timeframes=timeframes,
            candle_count=doctor_settings.volatility_window + doctor_settings.atr_period,
        )
        
        symbols_state: dict[str, Any] = {}
        
        for sym, data in res.instruments.items():
            symbols_state[sym] = {
                "symbol": sym,
                "candles": data.candles,
                "market_structure": None,
                "forecast": None,
                "candidates": [],
                "risk_assessments": {},
                "_tick": data.tick,
                "_symbol_info": data.symbol_info,
            }
        
        return {"symbols": symbols_state}

    builder.add_node("vision", vision_node)

    from jarvis.agents.fury import run_fury, FurySettings
    from langchain_anthropic import ChatAnthropic
    import os
    
    @safe_node("NickFury")
    def nick_fury_node(state: JarvisState) -> dict[str, Any]:
        llm = None
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if api_key:
            llm = ChatAnthropic(model="claude-3-haiku-20240307") # type: ignore
        
        symbols = list(state.get("symbols", {}).keys())
        impacts = run_fury(state["now"], symbols, FurySettings(), llm=llm)
        
        news_list = []
        for sym_impacts in impacts.values():
            news_list.extend(sym_impacts)
            
        return {"news": news_list}
    
    builder.add_node("nick_fury", nick_fury_node)

    def route_to_instruments(state: JarvisState) -> list[Send]:
        sends = []
        for sym, sym_state in state.get("symbols", {}).items():
            if sym in subgraphs:
                sends.append(Send(f"instrument_{sym}", sym_state))
        return sends

    for sym, sub in subgraphs.items():
        node_name = f"instrument_{sym}"
        def make_subgraph_node(compiled_sub: Any = sub) -> Callable[[SymbolState], dict[str, Any]]:
            def node(state: SymbolState) -> dict[str, Any]:
                config = {
                    "configurable": {
                        "tick": state.get("_tick"),
                        "symbol_info": state.get("_symbol_info"),
                        "account_equity": 10000.0,
                    }
                }
                result = compiled_sub.invoke(state, config=config)
                return {"symbols": {state["symbol"]: result}}
            return node
        
        builder.add_node(node_name, make_subgraph_node())

    # We need a node to collect before Jarvis
    def merge_instruments(state: JarvisState) -> dict[str, Any]:
        return {}
    builder.add_node("merge_instruments", merge_instruments)
    
    # Connect routing
    builder.add_conditional_edges("nick_fury", route_to_instruments, [f"instrument_{s}" for s in subgraphs.keys()])
    
    for sym in subgraphs.keys():
        builder.add_edge(f"instrument_{sym}", "merge_instruments")

    from jarvis.agents.jarvis import run_jarvis
    
    @safe_node("Jarvis")
    def jarvis_node(state: JarvisState) -> dict[str, Any]:
        signals = []
        news = state.get("news", [])
        
        for sym, sym_state in state.get("symbols", {}).items():
            # In a real run, llm could be injected via provider or config
            signal = run_jarvis(sym_state, news, jarvis_config, llm=None)
            if signal:
                signals.append(signal)
                
        return {"signals": signals}
    
    builder.add_node("jarvis", jarvis_node)
    
    builder.add_edge(START, "vision")
    builder.add_edge("vision", "nick_fury")
    builder.add_edge("merge_instruments", "jarvis")
    builder.add_edge("jarvis", END)

    return builder
