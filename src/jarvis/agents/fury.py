from datetime import datetime, timedelta

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
    symbol: str = Field(description="The trading instrument (e.g., XAUUSD, EURUSD) this news impacts. Must exactly match one of the requested symbols.")
    bias: str = Field(description="BULLISH, BEARISH, or NEUTRAL")
    impact: int = Field(description="Impact score from 0 to 10, where 10 is market-shaking (NFP, FOMC) and 0 is irrelevant.")
    is_high_impact_event: bool = Field(description="True if this is a major scheduled economic event like CPI, NFP, FOMC.")
    summary: str = Field(description="A 1-sentence summary of the news and its potential impact.")


class FuryOutput(BaseModel):
    classifications: list[NewsClassification]


def run_fury(
    now: datetime,
    symbols: list[str],
    settings: FurySettings,
    llm: BaseChatModel | None = None,
) -> dict[str, list[NewsImpact]]:
    """Fetch global news, classify impact per instrument, and determine blackouts."""
    
    # 1. Fetch RSS
    raw_news = []
    for url in settings.rss_urls:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:settings.max_items_per_feed]:
                title = getattr(entry, "title", "")
                summary = getattr(entry, "summary", getattr(entry, "description", ""))
                # Clean HTML or keep simple
                if title:
                    raw_news.append(f"Title: {title}\nSummary: {summary}")
        except Exception:
            # Silently skip failed feeds in production, or log them
            continue
            
    if not raw_news:
        return {sym: [] for sym in symbols}
        
    combined_news = "\n---\n".join(raw_news[:20]) # Limit to top 20 to save context
    
    impacts: dict[str, list[NewsImpact]] = {sym: [] for sym in symbols}
    
    # 2. Classify using LLM
    if llm is not None:
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert macro-economic news analyst. You read recent news headlines and classify their impact on specific trading instruments. Only output classifications for the provided instruments. Ignore irrelevant news."),
            ("human", "Target Instruments: {symbols}\n\nRecent News:\n{news}")
        ])
        try:
            chain = prompt | llm.with_structured_output(FuryOutput)
            result = chain.invoke({
                "symbols": ", ".join(symbols),
                "news": combined_news
            })
            
            # Handle both dict and BaseModel returns from structured output
            if isinstance(result, dict):
                classifications = result.get("classifications", [])
                for c in classifications:
                    sym = c.get("symbol")
                    if sym in symbols:
                        bias = c.get("bias", "NEUTRAL")
                        # map unknown bias to NEUTRAL
                        if bias not in ["BULLISH", "BEARISH", "NEUTRAL"]:
                            bias = "NEUTRAL"
                            
                        is_high = c.get("is_high_impact_event", False)
                        blackout = now + timedelta(minutes=settings.high_impact_blackout_minutes) if is_high else None
                        
                        impact = NewsImpact(
                            symbol=sym,
                            bias=bias,
                            impact=c.get("impact", 0),
                            blackout_until=blackout,
                            events=[], # We aren't mapping specific structured events yet
                            summary=c.get("summary", "")
                        )
                        impacts[sym].append(impact)
            elif hasattr(result, "classifications"):
                for c in result.classifications:
                    if c.symbol in symbols:
                        bias = c.bias
                        if bias not in ["BULLISH", "BEARISH", "NEUTRAL"]:
                            bias = "NEUTRAL"
                            
                        blackout = now + timedelta(minutes=settings.high_impact_blackout_minutes) if c.is_high_impact_event else None
                        
                        impact = NewsImpact(
                            symbol=c.symbol,
                            bias=bias,
                            impact=c.impact,
                            blackout_until=blackout,
                            events=[],
                            summary=c.summary
                        )
                        impacts[c.symbol].append(impact)
        except Exception:
            pass # On LLM failure, we return empty impacts
            
    return impacts
