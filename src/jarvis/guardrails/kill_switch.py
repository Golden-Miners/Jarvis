"""Kill switch for halting new cycles while allowing open signals to resolve."""

import contextvars
from dataclasses import dataclass
from enum import Enum

from jarvis.utils.logging import get_logger

log = get_logger(__name__)

# Contextvar for kill switch state (process-wide)
_kill_switch_var: contextvars.ContextVar[bool] = contextvars.ContextVar(
    "kill_switch", default=False
)

# Contextvar for kill switch metadata (reason, trigger)
_kill_switch_meta_var: contextvars.ContextVar[dict[str, str] | None] = contextvars.ContextVar(
    "kill_switch_meta", default=None
)


class KillSwitchTrigger(Enum):
    """Reasons for tripping the kill switch."""

    MANUAL = "manual"
    GUARDRAIL_VIOLATION = "guardrail_violation"
    CONSECUTIVE_FAILURES = "consecutive_failures"
    CONFIG_THRESHOLD = "config_threshold"
    DEPENDENCY_OUTAGE = "dependency_outage"


@dataclass
class KillSwitchStatus:
    """Kill switch status for reporting."""

    active: bool
    reason: str | None = None
    triggered_by: str | None = None


def get_kill_switch() -> bool:
    """Check if kill switch is currently tripped."""
    return _kill_switch_var.get()


def is_kill_switch_tripped() -> bool:
    """Alias for get_kill_switch for readability."""
    return get_kill_switch()


def get_kill_switch_status() -> KillSwitchStatus:
    """Get detailed kill switch status for logging/reporting."""
    meta = _kill_switch_meta_var.get()
    if meta:
        return KillSwitchStatus(
            active=True,
            reason=meta.get("reason"),
            triggered_by=meta.get("trigger"),
        )
    return KillSwitchStatus(active=_kill_switch_var.get())


def check_kill_switch_before_cycle() -> bool:
    """
    Check kill switch before starting a new cycle.
    Returns True if cycle should proceed, False if kill switch is active.
    """
    if _kill_switch_var.get():
        log.warning("cycle_blocked_kill_switch_active")
        return False
    return True


def trip_kill_switch(
    trigger: KillSwitchTrigger,
    details: str | None = None,
) -> None:
    """
    Trip the kill switch — halts NEW cycles only.
    Existing open signals continue resolving via Coulson.
    """
    if not _kill_switch_var.get():
        _kill_switch_var.set(True)
        _kill_switch_meta_var.set({
            "reason": details or f"Kill switch tripped: {trigger.value}",
            "trigger": trigger.value,
        })
        log.critical("kill_switch_tripped", trigger=trigger.value, details=details)
    else:
        log.warning("kill_switch_already_tripped", trigger=trigger.value)


def reset_kill_switch() -> None:
    """Reset the kill switch (for testing or manual recovery)."""
    _kill_switch_var.set(False)
    _kill_switch_meta_var.set(None)
    log.info("kill_switch_reset")


class KillSwitchContext:
    """
    Context manager for temporarily tripping the kill switch.
    Useful for testing.
    """

    def __init__(self, trigger: KillSwitchTrigger, details: str | None = None):
        self.trigger = trigger
        self.details = details
        self._was_tripped = False

    def __enter__(self) -> "KillSwitchContext":
        self._was_tripped = get_kill_switch()
        if not self._was_tripped:
            trip_kill_switch(self.trigger, self.details)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object | None,
    ) -> None:
        if not self._was_tripped:
            reset_kill_switch()