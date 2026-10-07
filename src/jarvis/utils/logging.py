"""Structured logging configuration using structlog."""

import contextvars
import sys

import structlog
from structlog.types import EventDict, WrappedLogger

# Module-level contextvar for cycle_id correlation
cycle_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar("cycle_id", default=None)


def add_cycle_id(logger: WrappedLogger, method_name: str, event_dict: EventDict) -> EventDict:
    """Add cycle_id from contextvars if available."""
    cycle_id = cycle_id_var.get()
    if cycle_id:
        event_dict["cycle_id"] = cycle_id
    return event_dict


def add_timestamp(logger: WrappedLogger, method_name: str, event_dict: EventDict) -> EventDict:
    """Add ISO timestamp."""
    from datetime import UTC, datetime
    event_dict["timestamp"] = datetime.now(UTC).isoformat()
    return event_dict


def redact_secrets(logger: WrappedLogger, method_name: str, event_dict: EventDict) -> EventDict:
    """Redact sensitive fields."""
    redacted_fields = {
        "password", "password_hash", "token", 
        "secret", "api_key", "mt5_password", "mt5_login"
    }
    for key in list(event_dict.keys()):
        if any(r in key.lower() for r in redacted_fields):
            event_dict[key] = "***REDACTED***"
    return event_dict


def configure_logging(
    level: str = "INFO",
    json_output: bool = True,
) -> None:
    """Configure structlog for JSON output with cycle_id correlation."""
    
    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        add_cycle_id,
        add_timestamp,
        redact_secrets,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
    ]
    
    if json_output:
        structlog.configure(
            processors=shared_processors + [
                structlog.processors.dict_tracebacks,
                structlog.processors.JSONRenderer(),
            ],
            wrapper_class=structlog.make_filtering_bound_logger(level),
            context_class=dict,
            logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
            cache_logger_on_first_use=True,
        )
    else:
        structlog.configure(
            processors=shared_processors + [
                structlog.dev.ConsoleRenderer(colors=True),
            ],
            wrapper_class=structlog.make_filtering_bound_logger(level),
            context_class=dict,
            logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
            cache_logger_on_first_use=True,
        )


def get_logger(name: str = "jarvis") -> structlog.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)  # type: ignore[no-any-return]


def set_cycle_id(cycle_id: str) -> None:
    """Set cycle_id in contextvars for correlation."""
    cycle_id_var.set(cycle_id)


def clear_cycle_id() -> None:
    """Clear cycle_id from contextvars."""
    cycle_id_var.set(None)


# Configure on import with defaults
configure_logging()