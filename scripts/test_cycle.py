import asyncio, sys
sys.path.insert(0, 'src')
from jarvis.config import load_instruments, load_jarvis, load_risk, load_sessions, load_strategies
from jarvis.config.models import DoctorStrangeSettings
from jarvis.data.mt5_provider import MT5Provider
from jarvis.db.store import SignalStore
from jarvis.graph.main_graph import build_main_graph
from jarvis.strategies import default_strategy_registry
from pathlib import Path
from datetime import UTC, datetime
from jarvis.db.session import DEFAULT_DB_PATH

async def test():
    instruments_config = load_instruments()
    strategies_config = load_strategies()
    jarvis_config = load_jarvis()
    risk_settings = load_risk()
    sessions_config = load_sessions()
    
    doctor_settings = DoctorStrangeSettings(
        primary_timeframe='M15',
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
    
    cache_dir = Path('data') / 'mt5_cache'
    cache_dir.mkdir(parents=True, exist_ok=True)
    db_path = DEFAULT_DB_PATH
    
    provider = MT5Provider(cache_dir=cache_dir)
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
    
    now = datetime.now(UTC)
    cycle_id = f'test-{now.strftime("%Y%m%d-%H%M%S")}'
    initial_state = {
        'cycle_id': cycle_id,
        'now': now,
        'news': [],
        'symbols': {},
        'signals': [],
        'errors': [],
        'outcomes': [],
    }
    
    print(f'Cycle ID: {cycle_id}')
    result = await compiled.ainvoke(initial_state)
    
    symbols = result.get('symbols', {})
    for sym, state in symbols.items():
        ms = state.get('market_structure')
        if ms:
            print(f'  {sym}: Trend={ms.timeframe_trends.get("M15", "N/A")}, ATR(M15)={ms.atr.get("M15", 0):.2f}')
    
    signals = result.get('signals', [])
    print(f'Signals generated: {len(signals)}')
    for s in signals:
        print(f'  SIGNAL: {s.symbol} {s.decision} {s.direction} @{s.entry:.5f} SL={s.sl:.5f} TP={s.tp:.5f} RR={s.rr:.2f} conf={s.confidence:.4f}')
    
    # Check database
    open_signals = store.get_open_signals()
    print(f'Open signals in DB: {len(open_signals)}')
    for s in open_signals:
        print(f'  DB: {s.symbol} {s.decision} {s.direction} @{s.entry:.5f} status={s.status}')
    
    # Check all signals
    all_signals = store.list_signals(limit=10)
    print(f'Total signals in DB: {len(all_signals)}')
    for s in all_signals:
        print(f'  DB: {s.symbol} {s.decision} {s.direction} @{s.entry:.5f} status={s.status} id={s.id}')
    
    all_signals = store.list_signals(limit=10)
    print(f'Total signals in DB: {len(all_signals)}')
    
    store.close()

asyncio.run(test())