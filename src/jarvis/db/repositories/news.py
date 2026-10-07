"""News item and impact persistence."""
# mypy: ignore-errors
from datetime import datetime

from sqlalchemy import select
from sqlmodel import Session

from jarvis.db.models import NewsImpactModel, NewsItemModel


def upsert_news_item(
    session: Session,
    *,
    id: str,
    source: str,
    url: str,
    url_hash: str,
    title: str,
    published_at: datetime,
    fetched_at: datetime,
    raw: str | None = None,
) -> NewsItemModel:
    """Insert or update a news item (deduped by url_hash)."""
    stmt = select(NewsItemModel).where(NewsItemModel.url_hash == url_hash)
    existing = session.exec(stmt).scalars().first()  # type: ignore
    if existing:
        existing.source = source
        existing.url = url
        existing.title = title
        existing.published_at = published_at
        existing.fetched_at = fetched_at
        existing.raw = raw
    else:
        existing = NewsItemModel(
            id=id,
            source=source,
            url=url,
            url_hash=url_hash,
            title=title,
            published_at=published_at,
            fetched_at=fetched_at,
            raw=raw,
        )
        session.add(existing)
    session.commit()
    return existing


def get_news_item(session: Session, id: str) -> NewsItemModel | None:
    """Fetch a news item by id."""
    return session.get(NewsItemModel, id)


def upsert_news_impact(
    session: Session,
    *,
    id: str,
    news_item_id: str,
    cycle_id: str,
    symbol: str,
    bias: str,
    impact: int,
    summary: str,
    model: str,
    created_at: datetime,
) -> NewsImpactModel:
    """Insert or update a news impact."""
    row = NewsImpactModel(
        id=id,
        news_item_id=news_item_id,
        cycle_id=cycle_id,
        symbol=symbol,
        bias=bias,
        impact=impact,
        summary=summary,
        model=model,
        created_at=created_at,
    )
    merged = session.merge(row)
    session.commit()
    return merged


def list_news_impacts(
    session: Session, cycle_id: str | None = None, symbol: str | None = None, limit: int = 100
) -> list[NewsImpactModel]:
    """List news impacts, optionally filtered."""
    stmt = select(NewsImpactModel)
    if cycle_id:
        stmt = stmt.where(NewsImpactModel.cycle_id == cycle_id)
    if symbol:
        stmt = stmt.where(NewsImpactModel.symbol == symbol)
    stmt = stmt.order_by(NewsImpactModel.created_at.desc()).limit(limit)
    return list(session.exec(stmt).scalars().all())  # type: ignore


def list_news_items(session: Session, limit: int = 100) -> list[NewsItemModel]:
    """Most recent news items first."""
    stmt = select(NewsItemModel).order_by(NewsItemModel.fetched_at.desc()).limit(limit)
    return list(session.exec(stmt).scalars().all())  # type: ignore