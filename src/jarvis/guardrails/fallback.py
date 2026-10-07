"""Deterministic fallback implementations for LLM guardrails."""

from datetime import datetime

from jarvis.guardrails.schemas import FuryOutput, NewsClassification
from jarvis.schemas.models import NewsImpact

# Keyword-based classification rules (symbol -> list of (keyword, bias, impact, is_high))
KEYWORD_RULES: dict[str, list[tuple[str, str, int, bool]]] = {
    "XAUUSD": [
        ("FED", "BEARISH", 8, True),
        ("RATE", "BEARISH", 7, True),
        ("INFLATION", "BULLISH", 7, True),
        ("CPI", "BULLISH", 8, True),
        ("PCE", "BULLISH", 7, True),
        ("GOLD", "BULLISH", 5, False),
        ("SAFE HAVEN", "BULLISH", 6, False),
        ("DOLLAR", "BEARISH", 6, False),
        ("YIELD", "BEARISH", 5, False),
    ],
    "XAGUSD": [
        ("FED", "BEARISH", 7, True),
        ("RATE", "BEARISH", 6, True),
        ("INDUSTRIAL", "BULLISH", 5, False),
        ("SILVER", "BULLISH", 5, False),
        ("MANUFACTURING", "BULLISH", 5, False),
    ],
    "BTCUSD": [
        ("ETF", "BULLISH", 8, True),
        ("REGULATION", "BEARISH", 7, True),
        ("SEC", "BEARISH", 6, True),
        ("ADOPTION", "BULLISH", 6, False),
        ("CRYPTO", "BULLISH", 5, False),
        ("BITCOIN", "BULLISH", 5, False),
        ("BLOCKCHAIN", "BULLISH", 4, False),
    ],
    "ETHUSD": [
        ("ETF", "BULLISH", 7, True),
        ("REGULATION", "BEARISH", 6, True),
        ("STAKING", "BULLISH", 5, False),
        ("ETHEREUM", "BULLISH", 5, False),
        ("DEFI", "BULLISH", 5, False),
        ("SMART CONTRACT", "BULLISH", 4, False),
    ],
    "USOUSD": [
        ("OPEC", "BULLISH", 8, True),
        ("CRUDE", "BULLISH", 6, False),
        ("OIL", "BULLISH", 6, False),
        ("INVENTORY", "BEARISH", 6, False),
        ("PRODUCTION", "BEARISH", 5, False),
        ("DEMAND", "BULLISH", 5, False),
    ],
}

DEFAULT_IMPACT = 3
DEFAULT_BIAS = "NEUTRAL"


def classify_news_keyword(
    title: str,
    summary: str,
    symbols: list[str],
) -> FuryOutput:
    """
    Deterministic keyword-based news classification.
    Used as fallback when LLM is unavailable or fails validation.
    """
    text = f"{title} {summary}".upper()
    classifications: list[NewsClassification] = []

    for symbol in symbols:
        rules = KEYWORD_RULES.get(symbol, [])
        best_match: NewsClassification | None = None
        best_impact = -1

        for keyword, bias, impact, is_high in rules:
            if keyword.upper() in text:
                if impact > best_impact:
                    best_impact = impact
                    best_match = NewsClassification(
                        symbol=symbol,
                        bias=bias,  # type: ignore[arg-type]
                        impact=impact,
                        is_high_impact_event=is_high,
                        summary=f"Keyword match: {keyword}",
                    )

        if best_match:
            classifications.append(best_match)
        else:
            # No keyword match - neutral classification
            classifications.append(NewsClassification(
                symbol=symbol,
                bias=DEFAULT_BIAS,  # type: ignore[arg-type]
                impact=DEFAULT_IMPACT,
                is_high_impact_event=False,
                summary="No keyword match - neutral",
            ))

    return FuryOutput(classifications=classifications)


def keyword_fallback_to_news_impact(
    fury_output: FuryOutput,
    now: datetime,
    blackout_minutes: int,
) -> dict[str, list[NewsImpact]]:
    """Convert FuryOutput to NewsImpact dict with blackout windows."""
    impacts: dict[str, list[NewsImpact]] = {}

    for c in fury_output.classifications:
        if c.symbol not in impacts:
            impacts[c.symbol] = []

        blackout = None
        if c.is_high_impact_event:
            from datetime import timedelta
            blackout = now + timedelta(minutes=blackout_minutes)

        impacts[c.symbol].append(NewsImpact(
            symbol=c.symbol,
            bias=c.bias,
            impact=c.impact,
            blackout_until=blackout,
            events=[],
            summary=c.summary,
        ))

    return impacts


# Rationale template for fallback
RATIONALE_TEMPLATE = (
    "Signal generated for {symbol} {direction} based on confluence of {count} factors:\n"
    "{breakdown}\n"
    "Agent verdicts: {verdicts}\n"
    "Score: {score:.2f} (min threshold: {min_score}).\n"
    "Entry: {entry:.5f} | SL: {sl:.5f} | TP: {tp:.5f} | RR: {rr:.2f}"
)

MINIMAL_RATIONALE_TEMPLATE = (
    "Signal for {symbol} {direction} — confluence score {score:.2f}. "
    "Entry {entry:.5f}, SL {sl:.5f}, TP {tp:.5f}. "
    "Rationale generated via template fallback."
)


def get_fallback_rationale(
    symbol: str,
    direction: str,
    score: float,
    score_breakdown: dict[str, float],
    agent_verdicts: dict[str, str],
) -> str:
    """Generate template-based rationale when LLM is unavailable."""
    # Use minimal template for brevity and reliability
    return MINIMAL_RATIONALE_TEMPLATE.format(
        symbol=symbol,
        direction=direction,
        score=score,
        entry=0.0,  # Will be filled by caller if needed
        sl=0.0,
        tp=0.0,
    )


def get_detailed_fallback_rationale(
    symbol: str,
    direction: str,
    score: float,
    score_breakdown: dict[str, float],
    agent_verdicts: dict[str, str],
    entry: float,
    sl: float,
    tp: float,
    rr: float,
) -> str:
    """Generate detailed template-based rationale with full trade parameters."""
    breakdown_parts = []
    for component, value in score_breakdown.items():
        if value > 0:
            breakdown_parts.append(f"{component}={value:.2f}")
    breakdown_str = "; ".join(breakdown_parts) if breakdown_parts else "none"

    verdicts_str = "; ".join(
        f"{k}: {v}" for k, v in agent_verdicts.items()
    ) if agent_verdicts else "none"

    return RATIONALE_TEMPLATE.format(
        symbol=symbol,
        direction=direction,
        count=len([v for v in score_breakdown.values() if v > 0]),
        breakdown=breakdown_str,
        verdicts=verdicts_str,
        score=score,
        min_score=1.0,  # Default, could be passed as param
        entry=entry,
        sl=sl,
        tp=tp,
        rr=rr,
    )