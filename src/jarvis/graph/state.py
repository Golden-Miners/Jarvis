from datetime import datetime
from typing import Annotated, Any, TypedDict

from jarvis.schemas import (
    Candle,
    Forecast,
    MarketStructure,
    NewsImpact,
    Outcome,
    RiskAssessment,
    SetupCandidate,
    Signal,
)


class AgentError(TypedDict):
    agent: str
    symbol: str | None
    error: str
    timestamp: datetime


def merge_list(left: list[Any] | None, right: list[Any] | Any | None) -> list[Any]:
    """Reducer for lists."""
    if left is None:
        if right is None:
            return []
        return right if isinstance(right, list) else [right]
    if right is None:
        return left
    return left + (right if isinstance(right, list) else [right])


def merge_dict(left: dict[Any, Any] | None, right: dict[Any, Any] | None) -> dict[Any, Any]:
    """Reducer for dicts."""
    if left is None:
        return right or {}
    if right is None:
        return left
    return {**left, **right}


class SymbolState(TypedDict, total=False):
    """State for a single instrument's subgraph."""
    symbol: str
    candles: dict[str, list[Candle]]
    market_structure: MarketStructure | None
    forecast: Forecast | None
    candidates: Annotated[list[SetupCandidate], merge_list]
    risk_assessments: Annotated[dict[str, RiskAssessment], merge_dict]
    _tick: Any
    _symbol_info: Any


class JarvisState(TypedDict, total=False):
    """Global state for the main graph."""
    cycle_id: str
    now: datetime
    news: list[NewsImpact]
    symbols: Annotated[dict[str, SymbolState], merge_dict]
    signals: Annotated[list[Signal], merge_list]
    outcomes: Annotated[list[Outcome], merge_list]
    errors: Annotated[list[AgentError], merge_list]
