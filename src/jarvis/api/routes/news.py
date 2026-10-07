"""News routes."""

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, col, desc, select

from jarvis.api.auth import UserInDB, require_viewer
from jarvis.api.schemas import (
    CalendarEventResponse,
    CalendarListResponse,
    NewsImpactResponse,
    NewsListResponse,
)
from jarvis.db.models import CalendarEventModel, NewsImpactModel, NewsItemModel
from jarvis.db.session import make_engine

router = APIRouter(prefix="/news", tags=["news"])


@router.get("", response_model=NewsListResponse)
async def list_news(
    limit: int = Query(50, ge=1, le=200),
    cursor: str | None = None,
    symbol: str | None = None,
    current_user: UserInDB = Depends(require_viewer),  # noqa: B008
) -> NewsListResponse:
    """List news items with impacts."""
    engine = make_engine()
    with Session(engine) as session:
        # Get news items with their impacts
        stmt = select(NewsItemModel)
        if cursor:
            stmt = stmt.where(NewsItemModel.fetched_at < datetime.fromisoformat(cursor))
        stmt = stmt.order_by(desc(col(NewsItemModel.fetched_at))).limit(limit + 1)
        news_items = list(session.exec(stmt).all())

        has_more = len(news_items) > limit
        if has_more:
            news_items = news_items[:limit]
            next_cursor = news_items[-1].fetched_at.isoformat() if news_items else None
        else:
            next_cursor = None

        # Get impacts for each news item
        results = []
        for item in news_items:
            impacts_stmt = select(NewsImpactModel).where(NewsImpactModel.news_item_id == item.id)
            if symbol:
                impacts_stmt = impacts_stmt.where(NewsImpactModel.symbol == symbol)
            impacts = list(session.exec(impacts_stmt).all())

            for impact in impacts:
                results.append(NewsImpactResponse(
                    id=impact.id,
                    source=item.source,
                    url=item.url,
                    symbol=impact.symbol,
                    bias=impact.bias,  # type: ignore
                    impact=impact.impact,
                    # blackout windows are carried by calendar_events, not news_impacts
                    blackout_until=None,
                    published_at=item.published_at.isoformat() if item.published_at else "",
                    summary=impact.summary,
                ))

    return NewsListResponse(data=results, next_cursor=next_cursor)


@router.get("/{symbol}", response_model=NewsListResponse)
async def news_for_symbol(
    symbol: str,
    limit: int = Query(50, ge=1, le=200),
    current_user: UserInDB = Depends(require_viewer),  # noqa: B008
) -> NewsListResponse:
    """Get news impacts for a specific symbol."""
    engine = make_engine()
    with Session(engine) as session:
        stmt = (
            select(NewsImpactModel, NewsItemModel)
            .join(NewsItemModel, col(NewsImpactModel.news_item_id) == col(NewsItemModel.id))
            .where(NewsImpactModel.symbol == symbol)
            .order_by(desc(col(NewsImpactModel.created_at)))
            .limit(limit)
        )
        results = list(session.exec(stmt).all())

        news_data = []
        for impact, item in results:
            news_data.append(NewsImpactResponse(
                id=impact.id,
                source=item.source,
                url=item.url,
                symbol=impact.symbol,
                bias=impact.bias,  # type: ignore
                impact=impact.impact,
                # blackout windows are carried by calendar_events, not news_impacts
                blackout_until=None,
                published_at=item.published_at.isoformat() if item.published_at else "",
                summary=impact.summary,
            ))

    return NewsListResponse(data=news_data, next_cursor=None)


@router.get("/calendar/events", response_model=CalendarListResponse)
async def list_calendar_events(
    limit: int = Query(100, ge=1, le=500),
    cursor: str | None = None,
    current_user: UserInDB = Depends(require_viewer),  # noqa: B008
) -> CalendarListResponse:
    """List upcoming calendar events with blackout windows."""
    engine = make_engine()
    with Session(engine) as session:
        stmt = select(CalendarEventModel)
        if cursor:
            stmt = stmt.where(CalendarEventModel.event_time < datetime.fromisoformat(cursor))
        stmt = stmt.order_by(desc(col(CalendarEventModel.event_time))).limit(limit + 1)
        events = list(session.exec(stmt).all())

        has_more = len(events) > limit
        if has_more:
            events = events[:limit]
            next_cursor = events[-1].event_time.isoformat() if events else None
        else:
            next_cursor = None

        return CalendarListResponse(
            data=[
                CalendarEventResponse(
                    id=e.id,
                    name=e.name,
                    currency=e.currency,
                    importance=e.importance,  # type: ignore
                    event_time=e.event_time.isoformat() if e.event_time else "",
                    blackout_start=e.blackout_start.isoformat() if e.blackout_start else None,
                    blackout_end=e.blackout_end.isoformat() if e.blackout_end else None,
                )
                for e in events
            ],
            next_cursor=next_cursor,
        )