"""The `schedule_at` of a message: a date-time in Romania time, the way the API reads it."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from functools import lru_cache
from typing import Final
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

#: The API reads schedule_at as Romania time.
SCHEDULE_TIMEZONE: Final = "Europe/Bucharest"

_EXPECTED: Final = 'schedule_at must be a timezone-aware datetime or a "YYYY-MM-DD HH:MM:SS" string, Romania time'


def format_schedule_at(schedule_at: datetime | str) -> str:
    """A date-time as the API wants it in schedule_at: `YYYY-MM-DD HH:MM:SS`, Romania time.

    A string is passed as is: the API refuses any other format with a 422.

    Raises:
        TypeError: when it is neither a datetime nor a string
        ValueError: when the datetime is naive: which time zone it is in cannot be known
    """
    if isinstance(schedule_at, str):
        return schedule_at

    if not isinstance(schedule_at, datetime):
        raise TypeError(f"{_EXPECTED}, got {type(schedule_at).__name__}.")

    if schedule_at.utcoffset() is None:
        raise ValueError(f"{_EXPECTED}; got a naive datetime, use e.g. datetime.now(timezone.utc).")

    local = to_romania_time(schedule_at)

    # Not strftime(): it does not pad years before 1000 on every platform
    return f"{local.year:04d}-{local.month:02d}-{local.day:02d} {local.hour:02d}:{local.minute:02d}:{local.second:02d}"


def to_romania_time(value: datetime) -> datetime:
    """A timezone-aware datetime converted to Romania time."""
    zone = _romania_zone()

    if zone is None:
        return romania_time_by_rule(value)

    return value.astimezone(zone)


@lru_cache(maxsize=1)
def _romania_zone() -> ZoneInfo | None:
    """Romania's time zone from the time zone database; None where there is none."""
    try:
        return ZoneInfo(SCHEDULE_TIMEZONE)
    except ZoneInfoNotFoundError:
        # Windows without the tzdata package, or a minimal container image
        return None


def romania_time_by_rule(value: datetime) -> datetime:
    """Romania time by the European Union's rule, which Romania follows since 1997.

    UTC+2 (EET), and UTC+3 (EEST) from the last Sunday of March to the last Sunday
    of October, the clocks changing at 01:00 UTC both times. Used only where no time
    zone database is installed.
    """
    utc = value.astimezone(timezone.utc)
    summer = _last_sunday(utc.year, 3) <= utc < _last_sunday(utc.year, 10)

    return utc.astimezone(timezone(timedelta(hours=3 if summer else 2)))


def _last_sunday(year: int, month: int) -> datetime:
    """The last Sunday of a month (March or October), at 01:00 UTC."""
    last_day = datetime(year, month + 1, 1, 1, tzinfo=timezone.utc) - timedelta(days=1)

    # weekday() counts from Monday (0) to Sunday (6)
    return last_day - timedelta(days=(last_day.weekday() + 1) % 7)
