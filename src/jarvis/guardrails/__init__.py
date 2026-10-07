"""JARVIS Guardrails — LLM output validation, repair, fallback, and kill switch."""

from jarvis.guardrails.fallback import (
    classify_news_keyword,
    get_fallback_rationale,
    keyword_fallback_to_news_impact,
)
from jarvis.guardrails.kill_switch import (
    KillSwitchContext,
    KillSwitchStatus,
    KillSwitchTrigger,
    check_kill_switch_before_cycle,
    get_kill_switch,
    get_kill_switch_status,
    is_kill_switch_tripped,
    reset_kill_switch,
    trip_kill_switch,
)
from jarvis.guardrails.schemas import (
    FuryOutput,
    NewsClassification,
    RationaleOutput,
    SchemaValidationError,
)

__all__ = [
    "FuryOutput",
    "NewsClassification",
    "RationaleOutput",
    "SchemaValidationError",
    "classify_news_keyword",
    "keyword_fallback_to_news_impact",
    "get_fallback_rationale",
    "KillSwitchContext",
    "KillSwitchStatus",
    "KillSwitchTrigger",
    "check_kill_switch_before_cycle",
    "get_kill_switch",
    "get_kill_switch_status",
    "is_kill_switch_tripped",
    "reset_kill_switch",
    "trip_kill_switch",
]