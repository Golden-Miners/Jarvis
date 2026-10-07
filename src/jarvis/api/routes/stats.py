"""Stats routes."""

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from jarvis.api.auth import UserInDB, require_viewer
from jarvis.api.schemas import StatsByInstrument, StatsResponse
from jarvis.db.models import OutcomeModel, SignalModel
from jarvis.db.session import make_engine

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("", response_model=StatsResponse)
async def get_stats(
    symbol: str | None = None,
    strategy: str | None = None,
    current_user: UserInDB = Depends(require_viewer),  # noqa: B008
):
    """Get win rate, avg R:R, expectancy by strategy and instrument."""
    engine = make_engine()
    with Session(engine) as session:
        # Base query: signals with outcomes
        base_stmt = (
            select(SignalModel, OutcomeModel)
            .join(OutcomeModel, SignalModel.id == OutcomeModel.signal_id)
            .where(SignalModel.decision == "TRADE")
        )
        if symbol:
            base_stmt = base_stmt.where(SignalModel.symbol == symbol)
        if strategy:
            # Filter by strategy from agent_verdicts or candidate
            pass  # Would need to join with setup_candidates

        results = list(session.exec(base_stmt).all())

        if not results:
            return StatsResponse(
                total_signals=0,
                win_rate=0.0,
                avg_rr=0.0,
                expectancy=0.0,
                by_strategy={},
                by_instrument={},
            )

        # Compute overall stats
        total = len(results)
        wins = sum(1 for s, o in results if o.result == "TP_HIT")
        losses = sum(1 for s, o in results if o.result == "SL_HIT")
        _ = sum(1 for s, o in results if o.result == "EXPIRED")

        win_rate = wins / (wins + losses) if (wins + losses) > 0 else 0.0
        avg_rr = sum(o.r_multiple for s, o in results) / total
        expectancy = (win_rate * avg_rr) - (1 - win_rate) if avg_rr > 0 else 0.0

        # By instrument
        by_inst = {}
        for s, o in results:
            key = s.symbol
            if key not in by_inst:
                by_inst[key] = {"wins": 0, "losses": 0, "total": 0, "rr_sum": 0.0}
            by_inst[key]["total"] += 1
            by_inst[key]["rr_sum"] += o.r_multiple
            if o.result == "TP_HIT":
                by_inst[key]["wins"] += 1
            elif o.result == "SL_HIT":
                by_inst[key]["losses"] += 1

        by_instrument = {}
        for sym, data in by_inst.items():
            total_closed = data["wins"] + data["losses"]
            wr = data["wins"] / total_closed if total_closed > 0 else 0.0
            by_instrument[sym] = StatsByInstrument(
                win_rate=wr,
                avg_rr=data["rr_sum"] / data["total"] if data["total"] > 0 else 0.0,
                count=data["total"],
            )

        # By strategy - would need to join with setup_candidates
        # Placeholder for now
        by_strategy = {}

        return StatsResponse(
            total_signals=total,
            win_rate=win_rate,
            avg_rr=avg_rr,
            expectancy=expectancy,
            by_strategy=by_strategy,
            by_instrument=by_instrument,
        )