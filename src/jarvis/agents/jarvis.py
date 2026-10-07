import math
import uuid
from datetime import UTC, datetime, timedelta

from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from pydantic import ValidationError

from jarvis.config.models import JarvisConfig
from jarvis.graph.state import SymbolState
from jarvis.guardrails import (
    RationaleOutput,
    SchemaValidationError,
    get_fallback_rationale,
)
from jarvis.schemas import Direction, NewsImpact, SetupCandidate, Signal
from jarvis.utils.logging import get_logger

log = get_logger(__name__)


def run_jarvis(
    symbol_state: SymbolState,
    news: list[NewsImpact],
    config: JarvisConfig,
    llm: BaseChatModel | None = None,
) -> Signal | None:
    """Evaluate confluence and generate a final trading Signal for a symbol."""
    symbol = symbol_state["symbol"]
    candidates = symbol_state.get("candidates", [])
    assessments = symbol_state.get("risk_assessments", {})
    structure = symbol_state.get("market_structure")
    forecast = symbol_state.get("forecast")

    if not candidates:
        return None

    # Helper to reconstruct ID
    def _cid(c: SetupCandidate) -> str:
        return (
            f"{c.symbol}:{c.strategy}:{c.created_at.isoformat()}"
            f":{c.direction}:{c.entry}:{c.sl}:{c.tp}"
        )

    # Filter candidates to valid ones
    valid_candidates = []
    for c in candidates:
        cid = _cid(c)
        assessment = assessments.get(cid)
        if assessment and assessment.valid:
            valid_candidates.append(c)

    if not valid_candidates:
        return None

    # Group by direction
    by_direction: dict[Direction, list[SetupCandidate]] = {}
    for c in valid_candidates:
        by_direction.setdefault(c.direction, []).append(c)

    best_signal: Signal | None = None
    best_score = -1.0

    # We evaluate both directions and pick the highest score
    for direction, direction_candidates in by_direction.items():
        # Score calculation
        score = 0.0
        score_breakdown: dict[str, float] = {}
        agent_verdicts: dict[str, str] = {}

        # 1. Strategies
        strat_score = 0.0
        for c in direction_candidates:
            val = c.confidence * config.w_strategy
            strat_score += val
            agent_verdicts[c.strategy] = f"Candidate provided ({c.confidence:.2f})"

        score += strat_score
        score_breakdown["strategies"] = strat_score

        # 2. Market Structure
        struct_score = 0.0
        if structure:
            trend = structure.timeframe_trends.get("primary", "RANGE")
            if (direction == "BUY" and trend == "UP") or (direction == "SELL" and trend == "DOWN"):
                struct_score = config.w_structure
                agent_verdicts["doctor_strange"] = f"Aligned with primary trend {trend}"
            else:
                agent_verdicts["doctor_strange"] = f"Neutral/Opposing primary trend {trend}"
            score += struct_score
            score_breakdown["structure"] = struct_score

        # 3. Forecast
        forecast_score = 0.0
        if forecast:
            if (direction == "BUY" and forecast.expected_direction == "UP") or \
               (direction == "SELL" and forecast.expected_direction == "DOWN"):
                forecast_score = config.w_forecast * forecast.strength
                agent_verdicts["quicksilver"] = f"Forecast aligned ({forecast.strength:.2f})"
            else:
                agent_verdicts["quicksilver"] = "Forecast neutral/opposing"
            score += forecast_score
            score_breakdown["forecast"] = forecast_score

        # 4. News
        news_score = 0.0
        if news:
            bullish = any(n.bias == "BULLISH" for n in news)
            bearish = any(n.bias == "BEARISH" for n in news)
            if direction == "BUY" and bullish and not bearish:
                news_score = config.w_news
                agent_verdicts["fury"] = "News is bullish"
            elif direction == "SELL" and bearish and not bullish:
                news_score = config.w_news
                agent_verdicts["fury"] = "News is bearish"
            else:
                agent_verdicts["fury"] = "News is mixed/neutral"
            score += news_score
            score_breakdown["news"] = news_score

        # Check thresholds
        meets_min_score = score >= config.min_score
        meets_min_agree = len(direction_candidates) >= config.min_agreeing_strategies
        if meets_min_score and meets_min_agree:
            if score > best_score:
                best_score = score
                # Pick the highest confidence candidate for entry/sl/tp
                best_cand = max(direction_candidates, key=lambda x: x.confidence)
                best_assessment = assessments[_cid(best_cand)]

                # Rationale with guardrails
                rationale = _generate_rationale_with_guardrails(
                    symbol=symbol,
                    direction=direction,
                    score=score,
                    score_breakdown=score_breakdown,
                    agent_verdicts=agent_verdicts,
                    llm=llm,
                )

                best_score_norm = 1.0 - math.exp(-best_score)
                best_signal = Signal(
                    id=str(uuid.uuid4()),
                    symbol=symbol,
                    decision="TRADE",
                    direction=direction,
                    entry=best_cand.entry,
                    sl=best_cand.sl,
                    tp=best_cand.tp,
                    rr=best_assessment.rr,
                    score=best_score,
                    confidence=best_score_norm,
                    score_breakdown=score_breakdown,
                    agent_verdicts=agent_verdicts,
                    rationale=rationale,
                    status="OPEN",
                    created_at=datetime.now(UTC),
                    expires_at=datetime.now(UTC)
                    + timedelta(seconds=config.cycle_interval_seconds * 4),
                )

    if best_signal:
        return best_signal

    return None


def _generate_rationale_with_guardrails(
    symbol: str,
    direction: str,
    score: float,
    score_breakdown: dict[str, float],
    agent_verdicts: dict[str, str],
    llm: BaseChatModel | None,
) -> str:
    """Generate rationale with schema validation, repair retry, and template fallback."""
    if llm is None:
        return get_fallback_rationale(
            symbol, direction, score, score_breakdown, agent_verdicts
        )

    _RATIONALE_SYSTEM_PROMPT = (
        "You are an expert trading supervisor. Provide a brief "
        "rationale for approving this trade. Be concise but comprehensive."
    )

    _RATIONALE_HUMAN_PROMPT = (
        "Symbol: {symbol}\nDirection: {direction}\n"
        "Score: {score}\nBreakdown: {breakdown}\n"
        "Verdicts: {verdicts}"
    )

    _RATIONALE_REPAIR_PROMPT = (
        "Your previous output failed schema validation. "
        "Error: {error}\n\n"
        "Please provide a valid rationale string (10-2000 characters, "
        "not a placeholder like 'n/a' or 'pending')."
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", _RATIONALE_SYSTEM_PROMPT),
        ("human", _RATIONALE_HUMAN_PROMPT),
    ])

    chain = prompt | llm.with_structured_output(RationaleOutput)

    # First attempt
    try:
        result = chain.invoke({
            "symbol": symbol,
            "direction": direction,
            "score": score,
            "breakdown": score_breakdown,
            "verdicts": agent_verdicts,
        })

        if isinstance(result, dict):
            rationale = str(result.get("rationale", ""))
        elif hasattr(result, "rationale"):
            rationale = str(result.rationale)
        else:
            raise SchemaValidationError(
                "Result missing 'rationale' field",
                schema_name="RationaleOutput",
            )

        # Validate through Pydantic
        validated = RationaleOutput(rationale=rationale)
        return validated.rationale

    except ValidationError as e:
        log.warning(
            "jarvis_rationale_validation_failed",
            error=str(e),
            symbol=symbol,
            attempt=1,
        )
    except Exception as e:
        log.warning(
            "jarvis_rationale_llm_error",
            error=str(e),
            error_type=type(e).__name__,
            symbol=symbol,
            attempt=1,
        )

    # ONE bounded repair retry
    repair_prompt = ChatPromptTemplate.from_messages([
        ("system", _RATIONALE_SYSTEM_PROMPT),
        ("human", _RATIONALE_HUMAN_PROMPT + "\n\n{repair_instruction}"),
    ])

    repair_chain = repair_prompt | llm.with_structured_output(RationaleOutput)

    try:
        repair_error_msg = (
            "Schema validation failed - rationale must be 10-2000 chars, "
            "not a placeholder"
        )
        result = repair_chain.invoke({
            "symbol": symbol,
            "direction": direction,
            "score": score,
            "breakdown": score_breakdown,
            "verdicts": agent_verdicts,
            "repair_instruction": _RATIONALE_REPAIR_PROMPT.format(
                error=repair_error_msg,
            ),
        })

        if isinstance(result, dict):
            rationale = str(result.get("rationale", ""))
        elif hasattr(result, "rationale"):
            rationale = str(result.rationale)
        else:
            raise SchemaValidationError(
                "Repair result missing 'rationale' field",
                schema_name="RationaleOutput",
            )

        # Validate through Pydantic
        validated = RationaleOutput(rationale=rationale)
        return validated.rationale

    except ValidationError as e:
        log.error(
            "jarvis_rationale_repair_failed",
            error=str(e),
            symbol=symbol,
            message="Repair retry failed - using template fallback",
        )
    except Exception as e:
        log.error(
            "jarvis_rationale_repair_error",
            error=str(e),
            error_type=type(e).__name__,
            symbol=symbol,
            message="Repair retry failed - using template fallback",
        )

    # Fallback to template
    log.info("jarvis_using_rationale_fallback", symbol=symbol)
    return get_fallback_rationale(
        symbol, direction, score, score_breakdown, agent_verdicts
    )