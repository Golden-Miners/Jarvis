"""Signals routes."""
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from jarvis.api.auth import UserInDB, require_viewer
from jarvis.api.schemas import (
    SignalDetailResponse,
    SignalListResponse,
    SignalResponse,
)
from jarvis.api.sse import broadcast_signal_created
from jarvis.db.models import SignalModel
from jarvis.db.repositories import signals as signals_repo
from jarvis.db.session import make_engine

router = APIRouter(prefix="/signals", tags=["signals"])


def _to_response(signal: SignalModel) -> SignalResponse:
    return SignalResponse(
        id=signal.id,
        symbol=signal.symbol,
        decision=signal.decision,  # type: ignore
        direction=signal.direction,  # type: ignore
        entry=signal.entry,
        sl=signal.sl,
        tp=signal.tp,
        rr=signal.rr,
        confidence=signal.confidence,
        score=signal.score,
        score_breakdown={},  # TODO: load from verdicts
        agent_verdicts={},  # TODO: load from verdicts
        rationale=signal.rationale,
        status=signal.status,  # type: ignore
        created_at=signal.created_at.isoformat() if signal.created_at else "",
        expires_at=signal.expires_at.isoformat() if signal.expires_at else "",
        no_trade_reason=signal.no_trade_reason,
    )


@router.get("", response_model=SignalListResponse)
async def list_signals(
    limit: int = Query(100, ge=1, le=500),
    cursor: str | None = None,
    symbol: str | None = None,
    status: str | None = None,
    decision: str | None = None,
    current_user: UserInDB = Depends(require_viewer),  # noqa: B008
):
    """List signals with filters and pagination."""
    engine = make_engine()
    with Session(engine) as session:
        stmt = select(SignalModel)
        if symbol:
            stmt = stmt.where(SignalModel.symbol == symbol)
        if status:
            stmt = stmt.where(SignalModel.status == status)
        if decision:
            stmt = stmt.where(SignalModel.decision == decision)
        if cursor:
            # Simple cursor-based pagination using created_at
            stmt = stmt.where(SignalModel.created_at < cursor)
        stmt = stmt.order_by(SignalModel.created_at.desc()).limit(limit + 1)
        results = list(session.exec(stmt).all())

    has_more = len(results) > limit
    if has_more:
        results = results[:limit]
        next_cursor = results[-1].created_at.isoformat() if results else None
    else:
        next_cursor = None

    return SignalListResponse(
        data=[_to_response(s) for s in results],
        next_cursor=next_cursor,
    )


@router.get("/open", response_model=SignalListResponse)
async def list_open_signals(
    symbol: str | None = None,
    current_user: UserInDB = Depends(require_viewer),  # noqa: B008
):
    """List all OPEN signals, optionally for one symbol."""
    engine = make_engine()
    with Session(engine) as session:
        open_signals = signals_repo.get_open_signals(session, symbol)

    return SignalListResponse(
        data=[_to_response(s) for s in open_signals],
        next_cursor=None,
    )


@router.get("/{signal_id}", response_model=SignalDetailResponse)
async def get_signal(
    signal_id: str,
    current_user: UserInDB = Depends(require_viewer),  # noqa: B008
):
    """Get signal detail with verdicts, candidate, and risk."""
    engine = make_engine()
    with Session(engine) as session:
        signal = session.get(SignalModel, signal_id)
        if not signal:
            raise HTTPException(status_code=404, detail="Signal not found")

        # TODO: Load verdicts, candidate, risk from their repositories
        return SignalDetailResponse(
            signal=_to_response(signal),
            verdicts=[],
            candidate=None,
            risk=None,
        )


# Internal function for graph to create signals
async def create_signal(signal_data: dict, cycle_id: str) -> SignalModel:
    """Create a new signal (called from graph)."""
    engine = make_engine()
    with Session(engine) as session:
        signal_model = SignalModel(
            id=signal_data["id"],
            cycle_id=cycle_id,
            symbol=signal_data["symbol"],
            decision=signal_data["decision"],
            direction=signal_data.get("direction"),
            entry=signal_data.get("entry"),
            sl=signal_data.get("sl"),
            tp=signal_data.get("tp"),
            rr=signal_data.get("rr"),
            confidence=signal_data["confidence"],
            score=signal_data["score"],
            no_trade_reason=signal_data.get("no_trade_reason"),
            rationale=signal_data["rationale"],
            status=signal_data["status"],
            created_at=datetime.fromisoformat(signal_data["created_at"].replace("Z", "+00:00")),
            expires_at=(
                datetime.fromisoformat(signal_data["expires_at"].replace("Z", "+00:00"))
                if signal_data.get("expires_at")
                else None
            ),
            updated_at=datetime.now(UTC),
        )
        session.add(signal_model)
        session.commit()
        session.refresh(signal_model)

    # Broadcast SSE event
    await broadcast_signal_created(_to_response(signal_model).model_dump())

    return signal_model