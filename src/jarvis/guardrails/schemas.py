"""Guardrail schemas for structured LLM outputs."""

from typing import Literal

from pydantic import BaseModel, Field

Bias = Literal["BULLISH", "BEARISH", "NEUTRAL"]


class NewsClassification(BaseModel):
    """Single news classification for one instrument."""

    model_config = {"extra": "forbid"}

    symbol: str
    bias: Bias
    impact: int = Field(ge=0, le=10)
    is_high_impact_event: bool
    summary: str = Field(min_length=1, max_length=500)


class FuryOutput(BaseModel):
    """Complete news classification output from Nick Fury."""

    model_config = {"extra": "forbid"}

    classifications: list[NewsClassification] = Field(default_factory=list)


class RationaleOutput(BaseModel):
    """Structured rationale output from Jarvis supervisor."""

    model_config = {"extra": "forbid"}

    rationale: str = Field(min_length=10, max_length=2000)


class SchemaValidationError(Exception):
    """Raised when LLM output fails schema validation and repair retry exhausted."""

    def __init__(
        self,
        message: str,
        schema_name: str,
        raw_output: str | None = None,
    ):
        super().__init__(message)
        self.schema_name = schema_name
        self.raw_output = raw_output or ""