"""Instruments routes."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlmodel import Session, select

from jarvis.api.auth import UserInDB, require_owner, require_viewer
from jarvis.db.models import InstrumentModel
from jarvis.db.repositories import signals as signals_repo
from jarvis.db.session import make_engine

router = APIRouter(prefix="/instruments", tags=["instruments"])


class InstrumentConfigResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    symbol: str
    broker_symbol: str
    agent_name: str
    digits: int | None = None
    point: float | None = None
    enabled: bool


class LatestDecisionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    symbol: str
    decision: str | None = None
    direction: str | None = None
    confidence: float | None = None
    status: str | None = None


class InstrumentUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    enabled: bool


@router.get("", response_model=list[InstrumentConfigResponse])
async def list_instruments(
    current_user: UserInDB = Depends(require_viewer),  # noqa: B008
) -> list[InstrumentConfigResponse]:
    """List all configured instruments."""
    engine = make_engine()
    with Session(engine) as session:
        instruments = session.exec(select(InstrumentModel)).all()
        return [
            InstrumentConfigResponse(
                symbol=i.symbol,
                broker_symbol=i.broker_symbol,
                agent_name=i.agent_name,
                digits=i.digits,
                point=i.point,
                enabled=bool(i.enabled),
            )
            for i in instruments
        ]


@router.get("/decisions", response_model=list[LatestDecisionResponse])
async def latest_decisions(
    current_user: UserInDB = Depends(require_viewer),  # noqa: B008
) -> list[LatestDecisionResponse]:
    """Get latest decision for each instrument."""
    engine = make_engine()
    with Session(engine) as session:
        instruments = session.exec(select(InstrumentModel)).all()
        results = []
        for inst in instruments:
            # Get latest signal for this symbol
            latest = signals_repo.get_open_signals(session, inst.symbol)
            latest_signal = latest[0] if latest else None

            results.append(LatestDecisionResponse(
                symbol=inst.symbol,
                decision=latest_signal.decision if latest_signal else None,
                direction=latest_signal.direction if latest_signal else None,
                confidence=latest_signal.confidence if latest_signal else None,
                status=latest_signal.status if latest_signal else None,
            ))
        return results


@router.patch("/{symbol}", response_model=InstrumentConfigResponse)
async def update_instrument(
    symbol: str,
    update: InstrumentUpdate,
    current_user: UserInDB = Depends(require_owner),  # noqa: B008
) -> InstrumentConfigResponse:
    """Enable/disable an instrument (OWNER only)."""
    engine = make_engine()
    with Session(engine) as session:
        instrument = session.get(InstrumentModel, symbol)
        if not instrument:
            raise HTTPException(status_code=404, detail="Instrument not found")
        instrument.enabled = 1 if update.enabled else 0
        session.commit()
        session.refresh(instrument)
        return InstrumentConfigResponse(
            symbol=instrument.symbol,
            broker_symbol=instrument.broker_symbol,
            agent_name=instrument.agent_name,
            digits=instrument.digits,
            point=instrument.point,
            enabled=bool(instrument.enabled),
        )