"""Run strategies on real MT5 data and report setup counts."""
import json
from datetime import UTC, datetime
from pathlib import Path

from jarvis.agents.instruments.black_panther import BlackPanther
from jarvis.agents.instruments.captain_america import CaptainAmerica
from jarvis.agents.instruments.hulk import Hulk
from jarvis.agents.instruments.iron_man import IronMan
from jarvis.agents.instruments.thor import Thor
from jarvis.agents.strange import run_strange
from jarvis.config.models import (
    DoctorStrangeSettings,
    InstrumentConfig,
    JarvisConfig,
    RiskSettings,
    StrategiesConfig,
    StrategyConfig,
)
from jarvis.graph.state import SymbolState
from jarvis.schemas import Candle, SymbolInfo, Tick
from jarvis.strategies import default_strategy_registry

FIXTURES_DIR = Path("data/real_fixtures")
SYMBOLS = ["XAUUSD", "XAGUSD", "BTCUSD", "ETHUSD", "USOUSD"]
TIMEFRAMES = ["M5", "M15", "H1", "H4", "D1"]
AGENT_MAP = {
    "XAUUSD": ("Iron Man", IronMan),
    "XAGUSD": ("Captain America", CaptainAmerica),
    "BTCUSD": ("Thor", Thor),
    "ETHUSD": ("Hulk", Hulk),
    "USOUSD": ("Black Panther", BlackPanther),
}


def load_candles(symbol: str) -> dict[str, list[Candle]]:
    """Load real fixture candles for a symbol."""
    candles_by_tf = {}
    for tf in TIMEFRAMES:
        filepath = FIXTURES_DIR / symbol / f"{tf}.json"
        if not filepath.exists():
            print(f"  {symbol} {tf}: file not found, skipping")
            continue
        with open(filepath) as f:
            data = json.load(f)
        if not data:
            continue
        candles = []
        for r in data:
            try:
                candles.append(Candle(
                    timestamp=datetime.fromisoformat(r["timestamp"]),
                    open=r["open"],
                    high=r["high"],
                    low=r["low"],
                    close=r["close"],
                    volume=r["volume"],
                ))
            except Exception as e:
                print(f"  {symbol} {tf}: error parsing candle: {e}")
                continue
        if candles:
            candles_by_tf[tf] = candles
            print(f"  {symbol} {tf}: loaded {len(candles)} candles")
    return candles_by_tf


def get_symbol_info(symbol: str) -> SymbolInfo:
    """Get symbol info from MT5."""
    import MetaTrader5 as mt5
    if not mt5.initialize():
        raise RuntimeError("MT5 init failed")
    info = mt5.symbol_info(symbol)
    mt5.shutdown()
    if info is None:
        raise ValueError(f"Symbol {symbol} not found in MT5")
    return SymbolInfo(
        symbol=symbol,
        digits=info.digits,
        point=info.point,
        trade_tick_size=info.trade_tick_size,
        trade_tick_value=info.trade_tick_value,
        volume_min=info.volume_min,
        volume_max=info.volume_max,
        volume_step=info.volume_step,
    )


def get_latest_tick(symbol: str) -> Tick:
    """Get latest tick from MT5."""
    import MetaTrader5 as mt5
    if not mt5.initialize():
        raise RuntimeError("MT5 init failed")
    tick = mt5.symbol_info_tick(symbol)
    mt5.shutdown()
    if tick is None:
        raise ValueError(f"Tick for {symbol} not found")
    return Tick(
        timestamp=datetime.fromtimestamp(tick.time, tz=UTC),
        bid=tick.bid,
        ask=tick.ask,
    )


def run_strategies_on_symbol(symbol: str, agent_name: str, AgentClass: type) -> None:
    print(f"\n{'='*60}")
    print(f"  {symbol} ({agent_name})")
    print(f"{'='*60}")
    
    # Load candles
    candles_by_tf = load_candles(symbol)
    if not candles_by_tf:
        print("  No candles loaded, skipping")
        return
    
    # Check required timeframes
    required = ["M15", "H1", "H4", "D1"]
    missing = [tf for tf in required if tf not in candles_by_tf]
    if missing:
        print(f"  Missing required timeframes: {missing}, skipping")
        return
    
    # Configs
    agent_cfg = InstrumentConfig(
        symbol=symbol,
        broker_symbol=symbol,
        agent=agent_name,
        sessions=[],
        atr_multipliers={},
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
        maximum_spread_points=1000.0,
    )
    strategies_config = StrategiesConfig(
        strategies=[
            StrategyConfig(name="hawkeye", weight=1.0, enabled=True, params={}),
            StrategyConfig(name="black_widow", weight=1.0, enabled=True, params={}),
            StrategyConfig(name="falcon", weight=1.0, enabled=True, params={}),
            StrategyConfig(name="ant_man", weight=1.0, enabled=True, params={}),
            StrategyConfig(name="wasp", weight=1.0, enabled=True, params={}),
        ]
    )
    jarvis_config = JarvisConfig(
        risk_percent=1.0,
        minimum_rr=1.5,
        min_score=0.1,
        min_agreeing_strategies=1,
        cycle_interval_seconds=900,
    )
    registry = default_strategy_registry()
    
    # Run Doctor Strange
    try:
        now = max(c[-1].timestamp for c in candles_by_tf.values() if c)
        print(f"  Analysis time: {now}")
        
        structure = run_strange(
            agent_cfg,
            candles_by_tf,
            doctor_settings,
            [],  # session windows
            now,
        )
        print(f"  Trend M15: {structure.timeframe_trends.get('M15')}")
        print(f"  Trend H1:  {structure.timeframe_trends.get('H1')}")
        print(f"  ATR M15:   {structure.atr.get('M15', 0):.4f}")
        print(f"  ATR H1:    {structure.atr.get('H1', 0):.4f}")
        print(f"  Vol regime: {structure.volatility_regime}")
        print(f"  Session:    {structure.session}")
        
    except Exception as e:
        print(f"  Doctor Strange failed: {e}")
        return
    
    # Get MT5 symbol info and tick
    try:
        sym_info = get_symbol_info(symbol)
        tick = get_latest_tick(symbol)
        print(f"  Tick: bid={tick.bid}, ask={tick.ask}, spread={(tick.ask-tick.bid)/sym_info.point:.0f}pts")
    except Exception as e:
        print(f"  MT5 data fetch failed: {e}")
        return
    
    # Run each strategy
    active_strategies = list(registry.create_enabled(strategies_config).values())
    for strat in active_strategies:
        try:
            ctx = SymbolState(
                symbol=symbol,
                candles=candles_by_tf,
                market_structure=structure,
                forecast=None,
                candidates=[],
                risk_assessments={},
                _tick=tick,
                _symbol_info=sym_info,
            )
            # Need latest timestamp from candles
            latest_ts = max(c[-1].timestamp for c in candles_by_tf.values() if c)
            
            from jarvis.strategies.context import StrategyContext
            strat_ctx = StrategyContext(
                symbol=symbol,
                candles=candles_by_tf,
                market_structure=structure,
                now=latest_ts,
            )
            candidates = strat.analyse(strat_ctx)
            
            if candidates:
                print(f"  {strat.name}: {len(candidates)} candidate(s)")
                for cand in candidates[:2]:  # show first 2
                    print(f"    {cand.direction} entry={cand.entry:.5f} sl={cand.sl:.5f} tp={cand.tp:.5f} conf={cand.confidence:.2f}")
                    if cand.evidence:
                        print(f"      evidence: {'; '.join(cand.evidence[:2])}")
            else:
                print(f"  {strat.name}: 0 candidates")
        except Exception as e:
            print(f"  {strat.name}: ERROR - {e}")
    
    # War Machine risk assessment on all candidates
    all_candidates = []
    for strat in active_strategies:
        try:
            strat_ctx = StrategyContext(
                symbol=symbol,
                candles=candles_by_tf,
                market_structure=structure,
                now=latest_ts,
            )
            all_candidates.extend(strat.analyse(strat_ctx))
        except Exception:
            pass
    
    if all_candidates:
        from jarvis.agents.war_machine import run_war_machine
        atr_m15 = structure.atr.get("M15", 1.0)
        print(f"\n  Risk Assessment (War Machine) on {len(all_candidates)} candidates:")
        for cand in all_candidates[:5]:
            mult = agent_cfg.atr_multipliers.get(cand.strategy, 1.0)
            assessment = run_war_machine(
                candidate=cand,
                tick=tick,
                symbol_info=sym_info,
                atr_value=atr_m15 * mult,
                account_equity=10000.0,
                jarvis_config=jarvis_config,
                risk_settings=risk_settings,
            )
            status = "VALID" if assessment.valid else "INVALID"
            print(f"  {cand.strategy}/{cand.direction}: {status} rr={assessment.rr:.2f} sl_atr={assessment.sl_atr_mult:.2f} spread_ok={assessment.spread_ok} lot={assessment.suggested_lot}")
            if assessment.issues:
                print(f"    issues: {assessment.issues}")
    else:
        print("\n  No candidates for risk assessment")


def main():
    print("Running strategies on real MT5 data...")
    for symbol, (agent_name, AgentClass) in AGENT_MAP.items():
        run_strategies_on_symbol(symbol, agent_name, AgentClass)


if __name__ == "__main__":
    main()