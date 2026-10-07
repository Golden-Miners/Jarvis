"""Nick Fury agent — news parsing and impact classification."""

from datetime import datetime, timedelta
from typing import Any

import feedparser  # type: ignore
from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from jarvis.schemas import NewsImpact


class FurySettings(BaseModel):
    """Configuration for Nick Fury."""

    rss_urls: list[str] = [
        "https://www.forexlive.com/feed/news",
    ]
    max_items_per_feed: int = 10
    high_impact_blackout_minutes: int = 60


class NewsClassification(BaseModel):
    """LLM-structured classification of a single news item."""

    symbol: str = Field(
        description=(
            "The trading instrument this news impacts. "
            "Must exactly match one of the requested symbols."
        ),
    )
    bias: str = Field(description="BULLISH, BEARISH, or NEUTRAL")
    impact: int = Field(
        description=(
            "Impact score 0-10. "
            "10 = market-shaking (NFP, FOMC), 0 = irrelevant."
        ),
    )
    is_high_impact_event: bool = Field(
        description=(
            "True for major scheduled economic events "
            "like CPI, NFP, FOMC."
        ),
    )
    summary: str = Field(
        description="One-sentence summary of the news impact.",
    )


class FuryOutput(BaseModel):
    """Wrapper for structured LLM output."""

    classifications: list[NewsClassification]


_SYSTEM_PROMPT = (
    "You are an expert macro-economic news analyst. "
    "You read recent news headlines and classify their impact "
    "on specific trading instruments. "
    "Only output classifications for the provided instruments. "
    "Ignore irrelevant news."
)


def _build_blackout(
    now: datetime,
    is_high: bool,
    minutes: int,
) -> datetime | None:
    """Return blackout deadline for high-impact events."""
    if is_high:
        return now + timedelta(minutes=minutes)
    return None


def run_fury(
    now: datetime,
    symbols: list[str],
    settings: FurySettings,
    llm: BaseChatModel | None = None,
) -> dict[str, list[NewsImpact]]:
    """Fetch global news, classify impact, determine blackouts."""
    # 1. Fetch RSS
    raw_news: list[str] = []
    for url in settings.rss_urls:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[: settings.max_items_per_feed]:
                title = getattr(entry, "title", "")
                summary = getattr(
                    entry, "summary",
                    getattr(entry, "description", ""),
                )
                if title:
                    raw_news.append(
                        f"Title: {title}\nSummary: {summary}",
                    )
        except Exception:
            continue

    if not raw_news:
        return {sym: [] for sym in symbols}

    # Cap at 20 items to limit LLM context
    combined_news = "\n---\n".join(raw_news[:20])
    impacts: dict[str, list[NewsImpact]] = {
        sym: [] for sym in symbols
    }

    # 2. Classify using LLM
    if llm is None:
        return impacts

    prompt = ChatPromptTemplate.from_messages([
        ("system", _SYSTEM_PROMPT),
        (
            "human",
            "Target Instruments: {symbols}\n\n"
            "Recent News:\n{news}",
        ),
    ])
    try:
        chain = prompt | llm.with_structured_output(FuryOutput)
        result = chain.invoke({
            "symbols": ", ".join(symbols),
            "news": combined_news,
        })

        classifications: list[dict[str, Any] | NewsClassification] = []
        if isinstance(result, dict):
            classifications = result.get("classifications", [])
        elif hasattr(result, "classifications"):
            classifications = result.classifications

        for c in classifications:
            if isinstance(c, dict):
                sym = c.get("symbol")
                bias = c.get("bias", "NEUTRAL")
                is_high = c.get("is_high_impact_event", False)
                imp = c.get("impact", 0)
                summ = c.get("summary", "")
            else:
                sym = c.symbol
                bias = c.bias
                is_high = c.is_high_impact_event
                imp = c.impact
                summ = c.summary

            if sym not in symbols:
                continue
            if bias not in ("BULLISH", "BEARISH", "NEUTRAL"):
                bias = "NEUTRAL"

            blackout = _build_blackout(
                now, is_high,
                settings.high_impact_blackout_minutes,
            )
            impacts[sym].append(NewsImpact(
                symbol=sym,
                bias=bias,
                impact=imp,
                blackout_until=blackout,
                events=[],
                summary=summ,
            ))
    except Exception:
        pass  # On LLM failure, return empty impacts

    return impacts
