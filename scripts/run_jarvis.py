#!/usr/bin/env python
"""Run JARVIS continuously: API server + scheduled M15 cycles until manually stopped."""

import signal
import sys
import threading
import time
from datetime import UTC, datetime

import uvicorn
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

sys.path.insert(0, "src")

from pathlib import Path

from jarvis.api.main import app
from jarvis.config import load_instruments, load_jarvis, load_risk, load_sessions, load_strategies
from jarvis.config.models import DoctorStrangeSettings
from jarvis.data.mt5_provider import MT5Provider
from jarvis.db.store import SignalStore
from jarvis.graph.main_graph import build_main_graph
from jarvis.strategies import default_strategy_registry

# Global state for graceful shutdown
_shutdown = False
_scheduler: BackgroundScheduler | None = None
_uvicorn_thread: threading.Thread | None = None


def signal_handler(signum: int, frame) -> None:
    """Handle shutdown signals."""
    global _shutdown
    print(f"\n[{datetime.now(UTC).isoformat()}] Shutdown signal received ({signum})")
    _shutdown = True


def run_cycle_job() -> None:
    """Scheduled job to run a full cycle."""
    print(f"\n[{datetime.now(UTC).isoformat()}] === SCHEDULED CYCLE START ===")
    import asyncio
    
    async def _run() -> None:
        # Load all configs
        instruments_config = load_instruments()
        strategies_config = load_strategies()
        jarvis_config = load_jarvis()
        risk_settings = load_risk()
        sessions_config = load_sessions()
        
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
        
        # Use main database for persistence (so dashboard can see signals)
        from jarvis.db.session import DEFAULT_DB_PATH
        cache_dir = Path("data") / "mt5_cache"
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
        cycle_id = f"scheduled-{now.strftime('%Y%m%d-%H%M%S')}"
        initial_state = {
            "cycle_id": cycle_id,
            "now": now,
            "news": [],
            "symbols": {},
            "signals": [],
            "errors": [],
            "outcomes": [],
        }
        
        print(f"  Cycle ID: {cycle_id}")
        
        # Broadcast cycle started via SSE
        from jarvis.api.sse import broadcast_cycle_status, broadcast_signal_created
        await broadcast_cycle_status({
            "cycle_id": cycle_id,
            "status": "RUNNING",
            "started_at": now.isoformat(),
        })
        
        try:
            result = await compiled.ainvoke(initial_state)
            
            # Print results summary
            symbols = result.get("symbols", {})
            for sym, state in symbols.items():
                ms = state.get("market_structure")
                if ms:
                    trend_m15 = ms.timeframe_trends.get('M15', 'N/A')
                    atr_m15 = ms.atr.get('M15', 0)
                    print(f"  {sym}: Trend={trend_m15}, ATR(M15)={atr_m15:.2f}, "
                          f"Vol={ms.volatility_regime}, Session={ms.session}")
                
                candidates = state.get("candidates", [])
                if candidates:
                    for c in candidates:
                        c_str = (f"{c.strategy}: {c.direction} "
                                 f"entry={c.entry:.5f} sl={c.sl:.5f} "
                                 f"tp={c.tp:.5f} conf={c.confidence:.2f}")
                        print(f"    {c_str}")
            
            signals = result.get("signals", [])
            if signals:
                for s in signals:
                    print(f"  SIGNAL: {s.symbol} {s.decision} {s.direction} "
                          f"@{s.entry:.5f} SL={s.sl:.5f} TP={s.tp:.5f} "
                          f"RR={s.rr:.2f} conf={s.confidence:.4f}")
                    # Broadcast signal.created SSE event
                    try:
                        await broadcast_signal_created(s.model_dump(mode="json"))
                    except Exception as broadcast_err:
                        print(f"  Warning: Failed to broadcast signal: {broadcast_err}")
            else:
                print("  No signals generated")
            
        except Exception as e:
            print(f"  ERROR: {e}")
            await broadcast_cycle_status({
                "cycle_id": cycle_id,
                "status": "FAILED",
                "error": str(e),
                "finished_at": datetime.now(UTC).isoformat(),
            })
            raise
        
        # Broadcast cycle completed
        await broadcast_cycle_status({
            "cycle_id": cycle_id,
            "status": "COMPLETED",
            "finished_at": datetime.now(UTC).isoformat(),
        })
        
        print(f"[{datetime.now(UTC).isoformat()}] === SCHEDULED CYCLE COMPLETE ===\n")
    
    try:
        asyncio.run(_run())
    except Exception as e:
        print(f"  ERROR in cycle: {e}")
        import traceback
        traceback.print_exc()


def run_uvicorn() -> None:
    """Run uvicorn server in a thread."""
    try:
        uvicorn.run(app, host="127.0.0.1", port=5180, log_level="info")
    except Exception as e:
        print(f"[Uvicorn ERROR] {e}")
        import traceback
        traceback.print_exc()


def main() -> None:
    """Main entry point - runs API + scheduler until Ctrl+C."""
    global _scheduler, _uvicorn_thread
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("=" * 60)
    print("JARVIS CONTINUOUS RUNNER")
    print("=" * 60)
    print(f"Start time: {datetime.now(UTC).isoformat()}")
    print("API: http://127.0.0.1:5180")
    print("Dashboard: http://localhost:5174 (run `npm run dev` in web/)")
    print("Press Ctrl+C to stop")
    print("=" * 60)
    
    # Start uvicorn in background thread
    _uvicorn_thread = threading.Thread(target=run_uvicorn, daemon=True)
    _uvicorn_thread.start()
    print("[+] API server started on http://127.0.0.1:5180")
    
    # Give API a moment to start
    time.sleep(2)
    
    # Initialize and start scheduler
    _scheduler = BackgroundScheduler(timezone=UTC)
    
    # Schedule on M15 close: minutes 0, 15, 30, 45
    _scheduler.add_job(
        run_cycle_job,
        CronTrigger(minute="0,15,30,45", timezone=UTC),
        id="m15_cycle",
        name="M15 Close Cycle",
        max_instances=1,
        coalesce=True,
        misfire_grace_time=60,
    )
    
    _scheduler.start()
    print("[+] Scheduler started - will run cycles at M15 close (0, 15, 30, 45 minutes)")
    print(f"    Next run: {_scheduler.get_job('m15_cycle').next_run_time}")
    
    # Also run an initial cycle on startup
    print("\n[+] Running initial cycle...")
    run_cycle_job()
    
    # Main loop - wait for shutdown
    try:
        while not _shutdown:
            time.sleep(1)
            if not _uvicorn_thread.is_alive():
                print("[ERROR] Uvicorn thread died!")
                break
    except KeyboardInterrupt:
        pass
    finally:
        print("\n[+] Shutting down...")
        
        if _scheduler:
            _scheduler.shutdown(wait=True)
            print("[+] Scheduler stopped")
        
        # uvicorn thread is daemon, will exit with main
        print("[+] API server stopped")
        
        print(f"\nStop time: {datetime.now(UTC).isoformat()}")
        print("JARVIS stopped cleanly.")


if __name__ == "__main__":
    main()