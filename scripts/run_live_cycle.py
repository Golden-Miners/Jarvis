"""Run ONE read-only live cycle for XAUUSD through the full graph (with relaxed min_agreeing_strategies=1)."""
import json
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from jarvis.config import (
    load_instruments,
    load_jarvis,
    load_risk,
    load_sessions,
    load_strategies,
)
from jarvis.config.models import DoctorStrangeSettings
from jarvis.data.mt5_provider import MT5Provider
from jarvis.db.store import SignalStore
from jarvis.graph.main_graph import build_main_graph
from jarvis.graph.state import JarvisState
from jarvis.strategies import default_strategy_registry


def main():
    print("=" * 60)
    print("JARVIS LIVE CYCLE — XAUUSD (min_agreeing_strategies=1)")
    print("=" * 60)
    
    # Load all configs
    print("\n[1/7] Loading configs...")
    instruments_config = load_instruments()
    strategies_config = load_strategies()
    jarvis_config = load_jarvis()
    risk_settings = load_risk()
    sessions_config = load_sessions()
    
    # Override for this test: allow single strategy to trigger signal
    jarvis_config.min_agreeing_strategies = 1
    jarvis_config.min_score = 1.0
    
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
    
    registry = default_strategy_registry()
    
    # Filter to just XAUUSD for this test run
    xau_inst = [i for i in instruments_config.instruments if i.symbol == "XAUUSD"]
    if not xau_inst:
        print("  ERROR: XAUUSD not in instruments config")
        return
    instruments_config.instruments = xau_inst
    
    print(f"  Instruments: {[i.symbol for i in instruments_config.instruments]}")
    print(f"  Strategies:  {[s.name for s in strategies_config.strategies]}")
    print(f"  Jarvis: min_score={jarvis_config.min_score}, w_strat={jarvis_config.w_strategy}, w_struct={jarvis_config.w_structure}, min_agree={jarvis_config.min_agreeing_strategies}")
    print(f"  Risk: min_sl_atr={risk_settings.minimum_sl_atr_multiple}, max_sl_atr={risk_settings.maximum_sl_atr_multiple}, max_spread={risk_settings.maximum_spread_points}")
    
    # Use temporary directories for MT5 cache and SQLite
    with tempfile.TemporaryDirectory() as cache_tmp, tempfile.TemporaryDirectory() as db_tmp:
        cache_dir = Path(cache_tmp)
        db_path = Path(db_tmp) / "jarvis.db"
        
        # Initialize MT5 provider
        print("\n[2/7] Initializing MT5 provider...")
        provider = MT5Provider(cache_dir=cache_dir)
        print("  MT5 initialized successfully")
        
        # Build the main graph
        print("\n[3/7] Building main graph...")
        store = SignalStore(db_path=db_path, instruments=instruments_config.instruments)
        
        graph = build_main_graph(
            instruments_config=instruments_config,
            strategies_config=strategies_config,
            jarvis_config=jarvis_config,
            doctor_settings=doctor_settings,
            risk_settings=risk_settings,
            sessions_config=sessions_config,
            registry=registry,
            provider=provider,
            store=store,
        )
        
        compiled = graph.compile()
        print("  Graph compiled successfully")
        
        # Run the cycle
        print("\n[4/7] Running Vision (fetch candles)...")
        now = datetime.now(UTC)
        initial_state: JarvisState = {
            "cycle_id": f"live-{now.strftime('%Y%m%d-%H%M%S')}",
            "now": now,
            "news": [],
            "symbols": {},
            "signals": [],
            "errors": [],
            "outcomes": [],
        }
        
        print(f"  Cycle ID: {initial_state['cycle_id']}")
        print(f"  Time: {now.isoformat()}")
        
        print("\n[5/7] Invoking graph (this may take 30-60s)...")
        result = compiled.invoke(initial_state)
        
        # Extract and print results
        print("\n[6/7] Results:")
        
        # Vision results
        symbols = result.get("symbols", {})
        for sym, state in symbols.items():
            ms = state.get("market_structure")
            if ms:
                print(f"\n  Doctor Strange ({sym}):")
                print(f"    Trends: {ms.timeframe_trends}")
                print(f"    ATR: {ms.atr}")
                print(f"    Vol regime: {ms.volatility_regime}")
                print(f"    Session: {ms.session}")
                print(f"    Last BOS: {ms.last_bos}")
                print(f"    Last CHoCH: {ms.last_choch}")
                print(f"    Key levels: {ms.key_levels[:5]}..." if len(ms.key_levels) > 5 else f"    Key levels: {ms.key_levels}")
            
            forecast = state.get("forecast")
            if forecast:
                print(f"\n  Quicksilver ({sym}):")
                print(f"    Direction: {forecast.expected_direction}")
                print(f"    Strength: {forecast.strength:.4f}")
                print(f"    Horizon: {forecast.horizon_bars} bars")
                print(f"    Median end: {forecast.median[-1]:.5f}" if forecast.median else "    Median: N/A")
            else:
                print(f"\n  Quicksilver ({sym}): None (TimesFM not loaded)")
            
            candidates = state.get("candidates", [])
            if candidates:
                print(f"\n  Strategy Candidates ({sym}): {len(candidates)}")
                for c in candidates:
                    print(f"    {c.strategy}: {c.direction} entry={c.entry:.5f} sl={c.sl:.5f} tp={c.tp:.5f} conf={c.confidence:.2f}")
                    if c.evidence:
                        print(f"      evidence: {c.evidence[:2]}")
            else:
                print(f"\n  Strategy Candidates ({sym}): 0")
            
            assessments = state.get("risk_assessments", {})
            if assessments:
                print(f"\n  War Machine ({sym}):")
                for aid, a in assessments.items():
                    status = "VALID" if a.valid else "INVALID"
                    print(f"    {aid}: {status} rr={a.rr:.2f} sl_atr={a.sl_atr_mult:.2f} spread_ok={a.spread_ok} lot={a.suggested_lot}")
                    if a.issues:
                        print(f"      issues: {a.issues}")
        
        # News
        news = result.get("news", [])
        print(f"\n  Nick Fury (News): {len(news)} items")
        for n in news:
            print(f"    {n.symbol}: bias={n.bias} impact={n.impact} summary={n.summary[:80]}...")
        
        # Signals
        signals = result.get("signals", [])
        print(f"\n  Jarvis (Supervisor): {len(signals)} signal(s)")
        for s in signals:
            print(f"    {s.symbol}: {s.decision} {s.direction or ''} conf={s.confidence:.4f} score={s.score:.4f}")
            print(f"      entry={s.entry} sl={s.sl} tp={s.tp} rr={s.rr}")
            print(f"      breakdown: {s.score_breakdown}")
            print(f"      verdicts: {s.agent_verdicts}")
            print(f"      rationale: {s.rationale}")
            print(f"      status: {s.status}")
        
        # Errors
        errors = result.get("errors", [])
        if errors:
            print(f"\n  Errors: {len(errors)}")
            for e in errors:
                print(f"    {e['agent']} ({e.get('symbol', 'global')}): {e['error']}")
        
        # Outcomes
        outcomes = result.get("outcomes", [])
        print(f"\n  Coulson (Outcomes): {len(outcomes)} resolved")
        for o in outcomes:
            print(f"    {o.signal_id}: {o.result} r={o.r_multiple:.2f} max_fav={o.max_favorable} max_adv={o.max_adverse}")
        
        # Save final signal to a JSON for Memory.md
        if signals:
            sig = signals[0]
            print("\n" + "=" * 60)
            print("FINAL SIGNAL (for Memory.md)")
            print("=" * 60)
            sig_dict = {
                "id": sig.id,
                "symbol": sig.symbol,
                "decision": sig.decision,
                "direction": sig.direction,
                "entry": sig.entry,
                "sl": sig.sl,
                "tp": sig.tp,
                "rr": sig.rr,
                "confidence": sig.confidence,
                "score": sig.score,
                "score_breakdown": sig.score_breakdown,
                "agent_verdicts": sig.agent_verdicts,
                "rationale": sig.rationale,
                "status": sig.status,
                "created_at": sig.created_at.isoformat(),
                "expires_at": sig.expires_at.isoformat(),
            }
            print(json.dumps(sig_dict, indent=2))
        else:
            print("\n  NO SIGNAL GENERATED")
        
        print("\n[7/7] Cycle complete")

        store.close()


if __name__ == "__main__":
    main()