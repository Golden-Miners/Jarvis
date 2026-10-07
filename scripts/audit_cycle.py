import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent / "src"))
from jarvis.agents.instruments.black_panther import BlackPanther
from jarvis.agents.instruments.captain_america import CaptainAmerica
from jarvis.agents.instruments.hulk import Hulk
from jarvis.agents.instruments.iron_man import IronMan
from jarvis.agents.instruments.thor import Thor
from jarvis.agents.strange import run_strange
from jarvis.config.models import ConfigManager
from jarvis.graph.state import SymbolState

SYMBOLS = ["XAUUSD", "XAGUSD", "BTCUSD", "ETHUSD", "USOUSD"]
AGENT_MAP = {
    "XAUUSD": IronMan,
    "XAGUSD": CaptainAmerica,
    "BTCUSD": Thor,
    "ETHUSD": Hulk,
    "USOUSD": BlackPanther,
}

def main():
    cm = ConfigManager(Path("config"))
    cm.load_configs()
    
    for symbol in SYMBOLS:
        print(f"\\n{'='*50}\\nRunning cycle for {symbol}\\n{'='*50}")
        agent_cls = AGENT_MAP[symbol]
        agent = agent_cls()
        agent.config = cm.get_instrument_config(symbol)
        
        state = SymbolState(
            symbol=symbol,
            timeframes={},
            market_structure=None,
            key_levels=None,
            forecast=None,
            setups=[],
            risk=None,
            signal=None,
            news=None,
            errors=[]
        )
        
        print("Running Doctor Strange...")
        state = run_strange(state)
        if state["errors"]:
            print(f"Errors in strange: {state['errors']}")
            continue
            
        print("Running Instrument agent (Strategies)...")
        # Find the agent node func
        for step in ["fetch_data", "analyze_structure", "find_setups", "assess_risk", "generate_signal"]:
            if hasattr(agent, step):
                print(f"  -> {step}")
                try:
                    func = getattr(agent, step)
                    state = func(state)
                except Exception as e:
                    print(f"Error in {step}: {e}")
                    import traceback
                    traceback.print_exc()
        
        setups = state.get("setups", [])
        print(f"Found {len(setups)} setups.")
        for s in setups:
            print(s.model_dump_json(indent=2))
            
        signal = state.get("signal")
        if signal:
            print(f"Generated Signal: {signal.model_dump_json(indent=2)}")
        else:
            print("No signal generated.")

if __name__ == "__main__":
    main()
