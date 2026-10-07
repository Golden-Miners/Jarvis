from typing import Any

from langgraph.constants import Send
from langgraph.graph import END, START, StateGraph

from jarvis.agents.coulson import run_coulson
from jarvis.agents.vision import run_vision
from jarvis.config.models import (
    DoctorStrangeSettings,
    InstrumentsConfig,
    JarvisConfig,
    RiskSettings,
    SessionsConfig,
    StrategiesConfig,
)
from jarvis.data.provider import DataProvider
from jarvis.db.store import SignalStore, config_hash
from jarvis.graph.instrument_graph import build_instrument_subgraph
from jarvis.graph.state import JarvisState, SymbolState
from jarvis.graph.wrapper import safe_node
from jarvis.guardrails import check_kill_switch_before_cycle, get_kill_switch_status
from jarvis.strategies.registry import StrategyRegistry
from jarvis.utils.logging import get_logger, set_cycle_id

log = get_logger(__name__)


def build_main_graph(
    instruments_config: InstrumentsConfig,
    strategies_config: StrategiesConfig,
    jarvis_config: JarvisConfig,
    doctor_settings: DoctorStrangeSettings,
    risk_settings: RiskSettings,
    sessions_config: SessionsConfig,
    registry: StrategyRegistry,
    provider: DataProvider,
    store: SignalStore | None = None,
) -> StateGraph[JarvisState]:

    # Build name -> SessionWindow mapping
    session_map = {sw.name: sw for sw in sessions_config.session_windows}

    subgraphs = {}
    for instrument in instruments_config.instruments:
        # Resolve session names to SessionWindow objects
        instrument_sessions = [
            session_map[name] for name in instrument.sessions if name in session_map
        ]
        subgraph = build_instrument_subgraph(
            instrument=instrument,
            strategies_config=strategies_config,
            jarvis_config=jarvis_config,
            doctor_settings=doctor_settings,
            risk_settings=risk_settings,
            session_windows=instrument_sessions,
            registry=registry,
        )
        subgraphs[instrument.symbol] = subgraph.compile()

    builder = StateGraph(JarvisState)

    @safe_node("KillSwitchCheck")
    def kill_switch_node(state: JarvisState) -> dict[str, Any]:
        """Check kill switch at cycle start - halts NEW cycles only."""
        if not check_kill_switch_before_cycle():
            # Kill switch active - return degraded status, no signals
            # Coulson will still resolve open signals
            status = get_kill_switch_status()
            log.warning(
                "cycle_halted_kill_switch_active",
                reason=status.reason,
                trigger=status.triggered_by,
            )
            return {
                "symbols": {},
                "news": [],
                "signals": [],
                "errors": [{
                    "agent": "KillSwitch",
                    "symbol": None,
                    "error": f"Cycle halted: {status.reason or 'Kill switch active'}",
                    "timestamp": state["now"],
                }],
            }
        return {}

    builder.add_node("kill_switch_check", kill_switch_node)

    @safe_node("Vision")
    def vision_node(state: JarvisState) -> dict[str, Any]:
        # Set cycle_id for log correlation
        set_cycle_id(state["cycle_id"])
        
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

    import os

    from langchain_anthropic import ChatAnthropic

    from jarvis.agents.fury import FurySettings, run_fury

    @safe_node("NickFury")
    def nick_fury_node(state: JarvisState) -> dict[str, Any]:
        llm = None
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if api_key:
            llm = ChatAnthropic(model="claude-3-haiku-20240307")  # type: ignore

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
        def make_subgraph_node(compiled_sub: Any = sub) -> Any:
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
    instrument_nodes = [f"instrument_{s}" for s in subgraphs.keys()]
    builder.add_conditional_edges("nick_fury", route_to_instruments, instrument_nodes)

    for sym in subgraphs.keys():
        builder.add_edge(f"instrument_{sym}", "merge_instruments")

    from jarvis.agents.jarvis import run_jarvis

    @safe_node("Jarvis")
    def jarvis_node(state: JarvisState) -> dict[str, Any]:
        signals = []
        news = state.get("news", [])

        for _sym, sym_state in state.get("symbols", {}).items():
            # In a real run, llm could be injected via provider or config
            signal = run_jarvis(sym_state, news, jarvis_config, llm=None)
            if signal:
                signals.append(signal)

        return {"signals": signals}

    builder.add_node("jarvis", jarvis_node)

    @safe_node("Coulson")
    def coulson_node(state: JarvisState) -> dict[str, Any]:
        if store is None:
            return {}
        ch = config_hash(instruments_config, strategies_config, jarvis_config)
        return run_coulson(
            state,
            store,
            doctor_settings.primary_timeframe,
            trigger="MANUAL",
            config_hash=ch,
        )

    builder.add_node("coulson", coulson_node)

    # Kill switch check runs FIRST, before vision
    builder.add_edge(START, "kill_switch_check")
    builder.add_edge("kill_switch_check", "vision")
    builder.add_edge("vision", "nick_fury")
    builder.add_edge("merge_instruments", "jarvis")
    builder.add_edge("jarvis", "coulson")
    builder.add_edge("coulson", END)

    return builder