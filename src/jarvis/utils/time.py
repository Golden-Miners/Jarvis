"""Time utilities for UTC handling."""

from datetime import UTC, datetime, timedelta


def now_utc() -> datetime:
    """Get current UTC time with timezone info."""
    return datetime.now(UTC)


def to_utc(dt: datetime) -> datetime:
    """Convert datetime to UTC, assuming naive datetimes are UTC."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def to_iso_utc(dt: datetime) -> str:
    """Convert datetime to ISO format UTC string."""
    return to_utc(dt).isoformat()


def from_iso_utc(s: str) -> datetime:
    """Parse ISO format UTC string to datetime."""
    dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
    return to_utc(dt)


def floor_to_minute(dt: datetime, minute: int = 1) -> datetime:
    """Floor datetime to nearest minute interval."""
    utc_dt = to_utc(dt)
    new_minute = (utc_dt.minute // minute) * minute
    return utc_dt.replace(minute=new_minute, second=0, microsecond=0)


def ceil_to_minute(dt: datetime, minute: int = 1) -> datetime:
    """Ceil datetime to nearest minute interval."""
    utc_dt = to_utc(dt)
    new_minute = ((utc_dt.minute + minute - 1) // minute) * minute
    if new_minute >= 60:
        return (utc_dt.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1))
    return utc_dt.replace(minute=new_minute, second=0, microsecond=0)


def next_m15_close(dt: datetime) -> datetime:
    """Get next M15 candle close time (15-min intervals)."""
    return ceil_to_minute(dt, 15)


def is_m15_close(dt: datetime) -> bool:
    """Check if datetime is at M15 close boundary (minute 0, 15, 30, 45)."""
    utc_dt = to_utc(dt)
    return utc_dt.minute % 15 == 0 and utc_dt.second == 0 and utc_dt.microsecond == 0


def session_name(dt: datetime) -> str:
    """Get session name for given UTC time.
    
    Sessions (provisional, need broker verification):
    - London: 07:00-16:00 UTC
    - New York: 12:00-21:00 UTC
    - Asian: 22:00-07:00 UTC (wraps midnight)
    - Crypto: 24/7
    """
    utc_dt = to_utc(dt)
    hour = utc_dt.hour
    
    if 7 <= hour < 16:
        return "london"
    elif 12 <= hour < 21:
        return "new_york"
    elif hour >= 22 or hour < 7:
        return "asian"
    else:
        return "transition"


def is_crypto_session() -> bool:
    """Crypto is 24/7."""
    return True


def format_duration_ms(start: datetime, end: datetime | None = None) -> int:
    """Calculate duration in milliseconds between two datetimes."""
    end_dt = end or now_utc()
    return int((end_dt - start).total_seconds() * 1000)