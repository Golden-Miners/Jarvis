"""Cycles routes."""
from datetime import UTC, datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlmodel import Session

from jarvis.api.auth import UserInDB, require_owner
from jarvis.api.schemas import CycleRunRequest, CycleRunResponse
from jarvis.api.sse import broadcast_cycle_status, broadcast_signal_created
from jarvis.db.repositories import cycles as cycles_repo
from jarvis.db.session import DEFAULT_DB_PATH, make_engine
from jarvis.graph.main_graph import build_main_graph

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
        graph = build_main_graph()
        initial_state = {
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
):
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
):
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


@router.get("", response_model=list[dict])
async def list_cycles(
    limit: int = Query(100, ge=1, le=500),
    current_user: UserInDB = Depends(require_owner),  # noqa: B008
):
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