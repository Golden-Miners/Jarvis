"""Nick Fury agent — news parsing and impact classification."""

from datetime import datetime, timedelta
from typing import Any

import feedparser  # type: ignore
from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from pydantic import ValidationError

from jarvis.guardrails import (
    FuryOutput,
    NewsClassification,
    SchemaValidationError,
    classify_news_keyword,
    keyword_fallback_to_news_impact,
)
from jarvis.schemas import NewsImpact
from jarvis.utils.logging import get_logger

log = get_logger(__name__)


class FurySettings:
    """Configuration for Nick Fury."""

    def __init__(
        self,
        rss_urls: list[str] | None = None,
        max_items_per_feed: int = 10,
        high_impact_blackout_minutes: int = 60,
    ):
        self.rss_urls = rss_urls or ["https://www.forexlive.com/feed/news"]
        self.max_items_per_feed = max_items_per_feed
        self.high_impact_blackout_minutes = high_impact_blackout_minutes


_SYSTEM_PROMPT = (
    "You are an expert macro-economic news analyst. "
    "You read recent news headlines and classify their impact "
    "on specific trading instruments. "
    "Only output classifications for the provided instruments. "
    "Ignore irrelevant news."
)

_REPAIR_PROMPT = (
    "Your previous output failed schema validation. "
    "Error: {error}\n\n"
    "Please fix the output to match the required schema exactly. "
    "Required fields for each classification: "
    "symbol (string, must match one of: {symbols}), "
    "bias (BULLISH/BEARISH/NEUTRAL), "
    "impact (integer 0-10), "
    "is_high_impact_event (boolean), "
    "summary (string)."
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


def _validate_and_convert(
    result: Any,
    symbols: list[str],
    now: datetime,
    settings: FurySettings,
) -> dict[str, list[NewsImpact]]:
    """Validate LLM output against FuryOutput schema and convert to NewsImpact."""
    impacts: dict[str, list[NewsImpact]] = {sym: [] for sym in symbols}

    # Handle both dict and object results
    if isinstance(result, dict):
        classifications = result.get("classifications", [])
    elif hasattr(result, "classifications"):
        classifications = result.classifications
    else:
        raise SchemaValidationError(
            "Result missing 'classifications' field",
            schema_name="FuryOutput",
            raw_output=str(result),
        )

    # Validate each classification through Pydantic model
    validated_classifications = []
    for c in classifications:
        if isinstance(c, dict):
            validated = NewsClassification(**c)
        else:
            validated = NewsClassification(
                symbol=c.symbol,
                bias=c.bias,
                impact=c.impact,
                is_high_impact_event=c.is_high_impact_event,
                summary=c.summary,
            )
        validated_classifications.append(validated)

    # Convert to NewsImpact
    for c in validated_classifications:
        if c.symbol not in symbols:
            log.warning("fury_symbol_mismatch", symbol=c.symbol, expected=symbols)
            continue

        blackout = _build_blackout(
            now, c.is_high_impact_event,
            settings.high_impact_blackout_minutes,
        )
        impacts[c.symbol].append(NewsImpact(
            symbol=c.symbol,
            bias=c.bias,
            impact=c.impact,
            blackout_until=blackout,
            events=[],
            summary=c.summary,
        ))

    return impacts


def _llm_classify_with_repair(
    llm: BaseChatModel,
    symbols: list[str],
    combined_news: str,
    now: datetime,
    settings: FurySettings,
) -> dict[str, list[NewsImpact]]:
    """Call LLM with structured output, with ONE bounded repair retry."""
    prompt = ChatPromptTemplate.from_messages([
        ("system", _SYSTEM_PROMPT),
        (
            "human",
            "Target Instruments: {symbols}\n\n"
            "Recent News:\n{news}",
        ),
    ])

    chain = prompt | llm.with_structured_output(FuryOutput)

    # First attempt
    try:
        result = chain.invoke({
            "symbols": ", ".join(symbols),
            "news": combined_news,
        })
        return _validate_and_convert(result, symbols, now, settings)
    except ValidationError as e:
        log.warning(
            "fury_schema_validation_failed",
            error=str(e),
            attempt=1,
        )
    except Exception as e:
        log.warning(
            "fury_llm_error",
            error=str(e),
            error_type=type(e).__name__,
            attempt=1,
        )

    # ONE bounded repair retry
    repair_prompt = ChatPromptTemplate.from_messages([
        ("system", _SYSTEM_PROMPT),
        (
            "human",
            "Target Instruments: {symbols}\n\n"
            "Recent News:\n{news}\n\n"
            "{repair_instruction}",
        ),
    ])

    repair_chain = repair_prompt | llm.with_structured_output(FuryOutput)

    try:
        result = repair_chain.invoke({
            "symbols": ", ".join(symbols),
            "news": combined_news,
            "repair_instruction": _REPAIR_PROMPT.format(
                error="Schema validation failed - check field types and required fields",
                symbols=", ".join(symbols),
            ),
        })
        return _validate_and_convert(result, symbols, now, settings)
    except ValidationError as e:
        log.error(
            "fury_repair_retry_failed",
            error=str(e),
            message="Repair retry failed schema validation - falling back to keyword matcher",
        )
        raise SchemaValidationError(
            "Repair retry failed",
            schema_name="FuryOutput",
            raw_output="",
        ) from e
    except Exception as e:
        log.error(
            "fury_repair_retry_error",
            error=str(e),
            error_type=type(e).__name__,
            message="Repair retry failed - falling back to keyword matcher",
        )
        raise


def run_fury(
    now: datetime,
    symbols: list[str],
    settings: FurySettings | None = None,
    llm: BaseChatModel | None = None,
) -> dict[str, list[NewsImpact]]:
    """Fetch global news, classify impact, determine blackouts."""
    if settings is None:
        settings = FurySettings()

    # 1. Fetch RSS
    raw_news: list[str] = []
    raw_entries: list[tuple[str, str]] = []  # (title, summary) for fallback
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
                    raw_entries.append((title, summary))
        except Exception:
            continue

    if not raw_news:
        return {sym: [] for sym in symbols}

    # Cap at 20 items to limit LLM context
    combined_news = "\n---\n".join(raw_news[:20])

    # 2. Classify using LLM with guardrails
    if llm is None:
        log.info("fury_no_llm_using_keyword_fallback")
        fury_output = classify_news_keyword("", "", symbols)
        return keyword_fallback_to_news_impact(
            fury_output, now, settings.high_impact_blackout_minutes
        )

    try:
        return _llm_classify_with_repair(llm, symbols, combined_news, now, settings)
    except SchemaValidationError:
        # Fallback to deterministic keyword matcher
        log.info("fury_using_keyword_fallback")
        fury_output = classify_news_keyword("", "", symbols)
        return keyword_fallback_to_news_impact(
            fury_output, now, settings.high_impact_blackout_minutes
        )
    except Exception as e:
        # Any other error (connection, timeout, etc.) - fallback
        log.error(
            "fury_llm_unavailable_fallback",
            error=str(e),
            error_type=type(e).__name__,
        )
        fury_output = classify_news_keyword("", "", symbols)
        return keyword_fallback_to_news_impact(
            fury_output, now, settings.high_impact_blackout_minutes
        )