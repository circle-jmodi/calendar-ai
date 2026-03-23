from datetime import datetime, date, time, timedelta
import pytz


def now_in_tz(timezone: str) -> datetime:
    tz = pytz.timezone(timezone)
    return datetime.now(tz)


def to_utc(dt: datetime, timezone: str) -> datetime:
    if dt.tzinfo is not None:
        return dt.astimezone(pytz.utc)
    tz = pytz.timezone(timezone)
    return tz.localize(dt).astimezone(pytz.utc)


def from_utc(dt: datetime, timezone: str) -> datetime:
    tz = pytz.timezone(timezone)
    if dt.tzinfo is None:
        dt = pytz.utc.localize(dt)
    return dt.astimezone(tz)


def date_range(start: date, days: int) -> list[date]:
    return [start + timedelta(days=i) for i in range(days)]


def combine_local(d: date, hour: int, minute: int, timezone: str) -> datetime:
    """Combine date + hour/minute into a timezone-aware UTC datetime."""
    tz = pytz.timezone(timezone)
    local_dt = tz.localize(datetime.combine(d, time(hour, minute)))
    return local_dt.astimezone(pytz.utc)


def parse_iso(s: str) -> datetime:
    """Parse ISO 8601 string to aware datetime."""
    return datetime.fromisoformat(s.replace("Z", "+00:00"))
