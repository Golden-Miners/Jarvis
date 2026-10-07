"""Cycles routes."""
from datetime import UTC, datetime
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlmodel import Session

from jarvis.api.auth import UserInDB, require_owner
from jarvis.api.schemas import CycleRunRequest, CycleRunResponse
from jarvis.api.sse import broadcast_cycle_status, broadcast_signal_created
from jarvis.config import (
    load_instruments,
    load_jarvis,
    load_risk,
    load_sessions,
    load_strategies,
)
from jarvis.config.models import DoctorStrangeSettings
from jarvis.data.mt5_provider import MT5Provider
from jarvis.db.repositories import cycles as cycles_repo
from jarvis.db.session import DEFAULT_DB_PATH, make_engine
from jarvis.db.store import SignalStore
from jarvis.graph.main_graph import build_main_graph
from jarvis.graph.state import JarvisState
from jarvis.strategies import default_strategy_registry

router = APIRouter(prefix="/cycles", tags=["cycles"])


async def run_cycle_background(cycle_id: str, config_hash: str, config_text: str) -> None:
    """Run the graph cycle in background."""
    engine = make_engine(DEFAULT_DB_PATH)
    with Session(engine) as session:
        cycles_repo.upsert_cycle(session, cycle_id, "MANUAL", config_hash, config_text)

    # Broadcast cycle started
    await broadcast_cycle_status({
        "cycle_id": cycle_id,
        "status": "RUNNING",
        "started_at": datetime.now(UTC).isoformat(),
    })

    try:
        # Build and run the graph
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

        cache_dir = Path("data") / "mt5_cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        provider = MT5Provider(cache_dir=cache_dir)
        store = SignalStore(
            db_path=DEFAULT_DB_PATH, instruments=instruments_config.instruments
        )

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
        ).compile()

        initial_state: JarvisState = {
            "cycle_id": cycle_id,
            "now": datetime.now(UTC),
            "news": [],
            "symbols": {},
            "signals": [],
            "errors": [],
            "outcomes": [],
        }
        result = await graph.ainvoke(initial_state)

        # Broadcast any new signals
        signals = result.get("signals", [])
        for s in signals:
            try:
                await broadcast_signal_created(s.model_dump())
            except Exception as broadcast_err:
                print(f"Warning: Failed to broadcast signal: {broadcast_err}")

        # Broadcast cycle completed
        await broadcast_cycle_status({
            "cycle_id": cycle_id,
            "status": "COMPLETED",
            "finished_at": datetime.now(UTC).isoformat(),
        })
    except Exception as e:
        await broadcast_cycle_status({
            "cycle_id": cycle_id,
            "status": "FAILED",
            "error": str(e),
            "finished_at": datetime.now(UTC).isoformat(),
        })


@router.post("/run", response_model=CycleRunResponse)
async def trigger_cycle(
    request: CycleRunRequest,
    background_tasks: BackgroundTasks,
    current_user: UserInDB = Depends(require_owner),  # noqa: B008
) -> CycleRunResponse:
    """Trigger a manual cycle run (OWNER only, rate-limited 1/min)."""
    import uuid
    cycle_id = f"cycle_{int(datetime.now(UTC).timestamp() * 1000)}_{uuid.uuid4().hex[:8]}"
    config_hash = "manual"  # In production, compute from actual config

    # Add to background tasks
    background_tasks.add_task(run_cycle_background, cycle_id, config_hash, "{}")

    return CycleRunResponse(
        cycle_id=cycle_id,
        status="RUNNING",
        message="Cycle started",
    )


@router.get("/{cycle_id}")
async def get_cycle(
    cycle_id: str,
    current_user: UserInDB = Depends(require_owner),  # noqa: B008
) -> dict[str, str | int | None]:
    """Get cycle details."""
    engine = make_engine()
    with Session(engine) as session:
        cycle = cycles_repo.get_cycle(session, cycle_id)
        if not cycle:
            raise HTTPException(status_code=404, detail="Cycle not found")

    return {
        "id": cycle.id,
        "trigger": cycle.trigger,
        "status": cycle.status,
        "config_hash": cycle.config_hash,
        "started_at": cycle.started_at.isoformat() if cycle.started_at else None,
        "finished_at": cycle.finished_at.isoformat() if cycle.finished_at else None,
        "duration_ms": cycle.duration_ms,
    }


@router.get("", response_model=list[dict[str, str | int | None]])
async def list_cycles(
    limit: int = Query(100, ge=1, le=500),
    current_user: UserInDB = Depends(require_owner),  # noqa: B008
) -> list[dict[str, str | int | None]]:
    """List recent cycles."""
    engine = make_engine()
    with Session(engine) as session:
        cycles_list = cycles_repo.list_cycles(session, limit)

    return [
        {
            "id": c.id,
            "trigger": c.trigger,
            "status": c.status,
            "config_hash": c.config_hash,
            "started_at": c.started_at.isoformat() if c.started_at else None,
            "finished_at": c.finished_at.isoformat() if c.finished_at else None,
            "duration_ms": c.duration_ms,
        }
        for c in cycles_list
    ]