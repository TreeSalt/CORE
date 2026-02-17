"""
cme_calendar.py — CME Regular Trading Hours Calendar
=====================================================
Implements CalendarAdapter for CME Group futures products.

Key rules:
  - RTH session: 08:30–16:00 CT (09:30–17:00 ET)
  - No new positions after 15:45 ET (close minus 15 min)
  - Mandatory flatten at 15:45 ET
  - Weekend/holiday handling (no trading Sat/Sun)

The 15:45 ET cutoff is the "Widowmaker Guard" — ensures all
positions are flattened before the last 15 minutes of highly
volatile session close, where slippage is catastrophic.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, time, timedelta, timezone

# ===========================================================
# Eastern Time helper (handles EST/EDT automatically)
# ===========================================================

# Fixed UTC offsets for US Eastern
_ET_STANDARD = timezone(timedelta(hours=-5))   # EST (Nov–Mar)
_ET_DAYLIGHT = timezone(timedelta(hours=-4))    # EDT (Mar–Nov)


def _is_dst(dt: datetime) -> bool:
    """
    Approximate US Eastern DST check.
    DST: second Sunday in March → first Sunday in November.
    This is a simplified heuristic; for production use pytz/zoneinfo.
    """
    year = dt.year

    # Second Sunday in March
    march_1 = datetime(year, 3, 1)
    days_until_sunday = (6 - march_1.weekday()) % 7
    dst_start = march_1 + timedelta(days=days_until_sunday + 7)  # 2nd Sunday
    dst_start = dst_start.replace(hour=2)

    # First Sunday in November
    nov_1 = datetime(year, 11, 1)
    days_until_sunday = (6 - nov_1.weekday()) % 7
    dst_end = nov_1 + timedelta(days=days_until_sunday)  # 1st Sunday
    dst_end = dst_end.replace(hour=2)

    naive = dt.replace(tzinfo=None)
    return dst_start <= naive < dst_end


def _to_et(dt: datetime) -> datetime:
    """Convert a datetime to US Eastern Time."""
    if dt.tzinfo is None:
        # Assume UTC for naive datetimes
        dt = dt.replace(tzinfo=timezone.utc)

    # Convert to UTC first
    utc_dt = dt.astimezone(timezone.utc)

    # Determine correct offset
    tz = _ET_DAYLIGHT if _is_dst(utc_dt) else _ET_STANDARD
    return utc_dt.astimezone(tz)


# ===========================================================
# Abstract Calendar Adapter
# ===========================================================

class CalendarAdapter(ABC):
    """
    Abstract calendar interface for trading session management.

    All times are passed as timezone-aware datetimes.
    Naive datetimes are treated as UTC.
    """

    @abstractmethod
    def is_trading_session(self, dt: datetime) -> bool:
        """True if dt falls within the regular trading session."""

    @abstractmethod
    def should_flatten(self, dt: datetime) -> bool:
        """True if all positions should be flattened (session end approaching)."""

    @abstractmethod
    def no_new_positions_after(self, dt: datetime) -> bool:
        """True if no new positions should be opened at this time."""


# ===========================================================
# CME Regular Trading Hours Calendar
# ===========================================================

# Session boundaries in ET
_RTH_OPEN = time(9, 30)     # 09:30 ET
_RTH_CLOSE = time(16, 0)    # 16:00 ET

# Widowmaker cutoff: 15 minutes before close
_CUTOFF = time(15, 45)      # 15:45 ET


class CMERTHCalendar(CalendarAdapter):
    """
    CME Regular Trading Hours (RTH) Calendar.

    Session: 09:30–16:00 ET
    No-new-positions cutoff: 15:45 ET (configurable)
    Flatten trigger: 15:45 ET (same as cutoff by default)

    The cutoff is configurable via `cutoff_minutes_before_close`:
      - Default: 15 minutes → 15:45 ET
      - Set to 0 to disable (allow trading until close)
    """

    def __init__(
        self,
        cutoff_minutes_before_close: int = 15,
        rth_open: time = _RTH_OPEN,
        rth_close: time = _RTH_CLOSE,
    ):
        self._rth_open = rth_open
        self._rth_close = rth_close
        self._cutoff_minutes = cutoff_minutes_before_close

        # Compute cutoff time
        close_dt = datetime.combine(datetime.today(), rth_close)
        cutoff_dt = close_dt - timedelta(minutes=cutoff_minutes_before_close)
        self._cutoff_time = cutoff_dt.time()

    @property
    def cutoff_time(self) -> time:
        """The no-new-positions cutoff time in ET."""
        return self._cutoff_time

    def is_trading_session(self, dt: datetime) -> bool:
        """True if dt is during RTH and on a weekday."""
        et = _to_et(dt)

        # Weekend check (Saturday=5, Sunday=6)
        if et.weekday() >= 5:
            return False

        current_time = et.time()
        return self._rth_open <= current_time < self._rth_close

    def should_flatten(self, dt: datetime) -> bool:
        """
        True if positions should be flattened.
        Triggers at or after the cutoff time during trading sessions.
        """
        et = _to_et(dt)

        # Only flatten during weekdays
        if et.weekday() >= 5:
            return False

        current_time = et.time()

        # Must be during the trading session
        if current_time < self._rth_open:
            return False

        # At or after cutoff → flatten
        return current_time >= self._cutoff_time

    def no_new_positions_after(self, dt: datetime) -> bool:
        """
        True if dt is at or after the cutoff time.
        This prevents opening new positions during the
        volatile close period.

        15:44 ET → False (allowed)
        15:45 ET → True  (blocked)
        15:46 ET → True  (blocked)
        """
        et = _to_et(dt)

        # Weekend → blocked
        if et.weekday() >= 5:
            return True

        current_time = et.time()

        # Before session → blocked
        if current_time < self._rth_open:
            return True

        # At or after cutoff → blocked
        return current_time >= self._cutoff_time
