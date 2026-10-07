"""Error types and codes for JARVIS system.

Error codes per Security_Access.md §7:
- AUTH_FAILED: Authentication/authorization failure
- VALIDATION_ERROR: Input validation failed
- DATA_STALE: Market data is stale or invalid
- DATA_GAP: Candle data has gaps/NaN/non-monotonic time
- MT5_CONNECTION: MT5 connection failed
- MT5_READ: MT5 read operation failed
- LLM_API: LLM API call failed
- LLM_AUTH: LLM authentication failed
- LLM_PARSE: LLM response parsing failed
- NEWS_FETCH: News feed fetch failed
- NEWS_PARSE: News parsing failed
- CALENDAR_FETCH: Economic calendar fetch failed
- TIMESFM_LOAD: TimesFM model load failed
- TIMESFM_FORECAST: TimesFM forecast generation failed
- GRAPH_EXECUTION: Graph node execution failed
- CONFIG_MISSING: Required configuration missing
- CONFIG_INVALID: Configuration validation failed
- INTERNAL_ERROR: Unexpected internal error
"""

from enum import StrEnum
from typing import Any


class ErrorCode(StrEnum):
    """Standardized error codes for JARVIS."""
    AUTH_FAILED = "AUTH_FAILED"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    DATA_STALE = "DATA_STALE"
    DATA_GAP = "DATA_GAP"
    MT5_CONNECTION = "MT5_CONNECTION"
    MT5_READ = "MT5_READ"
    LLM_API = "LLM_API"
    LLM_AUTH = "LLM_AUTH"
    LLM_PARSE = "LLM_PARSE"
    NEWS_FETCH = "NEWS_FETCH"
    NEWS_PARSE = "NEWS_PARSE"
    CALENDAR_FETCH = "CALENDAR_FETCH"
    TIMESFM_LOAD = "TIMESFM_LOAD"
    TIMESFM_FORECAST = "TIMESFM_FORECAST"
    GRAPH_EXECUTION = "GRAPH_EXECUTION"
    CONFIG_MISSING = "CONFIG_MISSING"
    CONFIG_INVALID = "CONFIG_INVALID"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class JarvisError(Exception):
    """Base exception for JARVIS errors with structured error code."""
    
    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.INTERNAL_ERROR,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.details = details or {}
    
    def __str__(self) -> str:
        return f"[{self.code.value}] {super().__str__()}"
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for logging/API responses."""
        return {
            "error": self.code.value,
            "message": super().__str__(),
            "details": self.details,
        }


class ValidationError(JarvisError):
    """Input validation error."""
    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message, ErrorCode.VALIDATION_ERROR, details)


class DataStaleError(JarvisError):
    """Market data is stale or invalid."""
    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message, ErrorCode.DATA_STALE, details)


class DataGapError(JarvisError):
    """Candle data has gaps/NaN/non-monotonic time."""
    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message, ErrorCode.DATA_GAP, details)


class MT5ConnectionError(JarvisError):
    """MT5 connection failed."""
    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message, ErrorCode.MT5_CONNECTION, details)


class MT5ReadError(JarvisError):
    """MT5 read operation failed."""
    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message, ErrorCode.MT5_READ, details)


class LLMAPIError(JarvisError):
    """LLM API call failed."""
    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message, ErrorCode.LLM_API, details)


class LLMAuthError(JarvisError):
    """LLM authentication failed."""
    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message, ErrorCode.LLM_AUTH, details)


class LLMParseError(JarvisError):
    """LLM response parsing failed."""
    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message, ErrorCode.LLM_PARSE, details)


class NewsFetchError(JarvisError):
    """News feed fetch failed."""
    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message, ErrorCode.NEWS_FETCH, details)


class NewsParseError(JarvisError):
    """News parsing failed."""
    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message, ErrorCode.NEWS_PARSE, details)


class CalendarFetchError(JarvisError):
    """Economic calendar fetch failed."""
    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message, ErrorCode.CALENDAR_FETCH, details)


class TimesFMLoadError(JarvisError):
    """TimesFM model load failed."""
    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message, ErrorCode.TIMESFM_LOAD, details)


class TimesFMForecastError(JarvisError):
    """TimesFM forecast generation failed."""
    def __init__(self, message: str, details: dict[str, Any] | None) -> None:
        super().__init__(message, ErrorCode.TIMESFM_FORECAST, details)


class GraphExecutionError(JarvisError):
    """Graph node execution failed."""
    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message, ErrorCode.GRAPH_EXECUTION, details)


class ConfigMissingError(JarvisError):
    """Required configuration missing."""
    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message, ErrorCode.CONFIG_MISSING, details)


class ConfigInvalidError(JarvisError):
    """Configuration validation failed."""
    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message, ErrorCode.CONFIG_INVALID, details)