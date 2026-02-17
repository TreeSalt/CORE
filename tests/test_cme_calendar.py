"""
test_cme_calendar.py — CME RTH Calendar Cutoff Tests
=====================================================
Verifies the 15:45 ET no-new-positions cutoff and flatten trigger.

Key test cases:
  - 15:44 ET → ALLOWED (no cutoff)
  - 15:45 ET → BLOCKED (cutoff active)
  - 15:46 ET → BLOCKED (past cutoff)
  - Weekend → BLOCKED
  - Pre-session → BLOCKED
  - Mid-session → ALLOWED

All times are passed as UTC and converted internally.
"""

import pytest
from datetime import datetime, timezone, timedelta

from antigravity_harness.calendar.cme_calendar import (
    CMERTHCalendar,
    CalendarAdapter,
    _to_et,
    _ET_STANDARD,
)


@pytest.fixture
def calendar():
    """Standard CME RTH calendar with 15-minute cutoff."""
    return CMERTHCalendar(cutoff_minutes_before_close=15)


# ===========================================================
# Helper: Create UTC datetime for a specific ET time
# ===========================================================

def _utc_for_et(hour, minute, year=2026, month=1, day=15):
    """
    Create a UTC datetime corresponding to the given ET time.
    January = EST (UTC-5), so 15:44 ET = 20:44 UTC.
    Using a Wednesday to avoid weekend issues.
    """
    # Jan 15, 2026 is a Thursday (weekday)
    et_offset = timedelta(hours=-5)  # EST in January
    et_dt = datetime(year, month, day, hour, minute, tzinfo=timezone(et_offset))
    return et_dt.astimezone(timezone.utc)


def _utc_for_edt(hour, minute, year=2026, month=6, day=17):
    """
    Create a UTC datetime corresponding to the given EDT time.
    June = EDT (UTC-4), so 15:44 EDT = 19:44 UTC.
    Using a Wednesday to avoid weekend issues.
    """
    edt_offset = timedelta(hours=-4)  # EDT in June
    et_dt = datetime(year, month, day, hour, minute, tzinfo=timezone(edt_offset))
    return et_dt.astimezone(timezone.utc)


# ===========================================================
# Core Cutoff Tests (EST — January)
# ===========================================================

class TestCutoffEST:
    """Test cutoff behavior during EST (winter)."""

    def test_1544_et_allows_new_positions(self, calendar):
        """15:44 ET → allowed — one minute before cutoff."""
        dt = _utc_for_et(15, 44)
        assert calendar.no_new_positions_after(dt) is False
        assert calendar.should_flatten(dt) is False

    def test_1545_et_blocks_new_positions(self, calendar):
        """15:45 ET → BLOCKED — exact cutoff boundary."""
        dt = _utc_for_et(15, 45)
        assert calendar.no_new_positions_after(dt) is True
        assert calendar.should_flatten(dt) is True

    def test_1546_et_blocks_new_positions(self, calendar):
        """15:46 ET → BLOCKED — past cutoff."""
        dt = _utc_for_et(15, 46)
        assert calendar.no_new_positions_after(dt) is True
        assert calendar.should_flatten(dt) is True

    def test_1559_et_blocks(self, calendar):
        """15:59 ET → BLOCKED — final minute of session."""
        dt = _utc_for_et(15, 59)
        assert calendar.no_new_positions_after(dt) is True

    def test_1000_et_allows(self, calendar):
        """10:00 ET → ALLOWED — mid-session."""
        dt = _utc_for_et(10, 0)
        assert calendar.no_new_positions_after(dt) is False
        assert calendar.should_flatten(dt) is False

    def test_0930_et_allows(self, calendar):
        """09:30 ET → ALLOWED — session open."""
        dt = _utc_for_et(9, 30)
        assert calendar.no_new_positions_after(dt) is False


# ===========================================================
# Core Cutoff Tests (EDT — June)
# ===========================================================

class TestCutoffEDT:
    """Test cutoff behavior during EDT (summer)."""

    def test_1544_edt_allows(self, calendar):
        """15:44 EDT → allowed."""
        dt = _utc_for_edt(15, 44)
        assert calendar.no_new_positions_after(dt) is False
        assert calendar.should_flatten(dt) is False

    def test_1545_edt_blocks(self, calendar):
        """15:45 EDT → BLOCKED."""
        dt = _utc_for_edt(15, 45)
        assert calendar.no_new_positions_after(dt) is True
        assert calendar.should_flatten(dt) is True

    def test_1546_edt_blocks(self, calendar):
        """15:46 EDT → BLOCKED."""
        dt = _utc_for_edt(15, 46)
        assert calendar.no_new_positions_after(dt) is True
        assert calendar.should_flatten(dt) is True


# ===========================================================
# Session Boundary Tests
# ===========================================================

class TestSessionBoundaries:
    """Test trading session window detection."""

    def test_during_session(self, calendar):
        dt = _utc_for_et(12, 0)
        assert calendar.is_trading_session(dt) is True

    def test_before_session(self, calendar):
        dt = _utc_for_et(9, 0)
        assert calendar.is_trading_session(dt) is False

    def test_at_open(self, calendar):
        dt = _utc_for_et(9, 30)
        assert calendar.is_trading_session(dt) is True

    def test_at_close(self, calendar):
        """16:00 ET is NOT in session (close is exclusive)."""
        dt = _utc_for_et(16, 0)
        assert calendar.is_trading_session(dt) is False

    def test_pre_session_blocks_new_positions(self, calendar):
        """Before session open → no new positions."""
        dt = _utc_for_et(8, 0)
        assert calendar.no_new_positions_after(dt) is True

    def test_weekend_saturday(self, calendar):
        """Saturday → not a trading session."""
        # Jan 17, 2026 is Saturday
        dt = _utc_for_et(12, 0, day=17)
        assert calendar.is_trading_session(dt) is False
        assert calendar.no_new_positions_after(dt) is True

    def test_weekend_sunday(self, calendar):
        """Sunday → not a trading session."""
        # Jan 18, 2026 is Sunday
        dt = _utc_for_et(12, 0, day=18)
        assert calendar.is_trading_session(dt) is False


# ===========================================================
# Calendar Adapter Contract Tests
# ===========================================================

class TestCalendarContract:
    """Verify CMERTHCalendar satisfies CalendarAdapter contract."""

    def test_is_subclass(self):
        assert issubclass(CMERTHCalendar, CalendarAdapter)

    def test_instance(self, calendar):
        assert isinstance(calendar, CalendarAdapter)

    def test_cutoff_time_is_1545(self, calendar):
        from datetime import time
        assert calendar.cutoff_time == time(15, 45)

    def test_custom_cutoff(self):
        """Custom cutoff of 30 minutes → 15:30 ET."""
        cal = CMERTHCalendar(cutoff_minutes_before_close=30)
        from datetime import time
        assert cal.cutoff_time == time(15, 30)

        # 15:29 ET → allowed
        dt = _utc_for_et(15, 29)
        assert cal.no_new_positions_after(dt) is False

        # 15:30 ET → blocked
        dt = _utc_for_et(15, 30)
        assert cal.no_new_positions_after(dt) is True


# ===========================================================
# ET Conversion Tests
# ===========================================================

class TestETConversion:
    """Verify timezone conversion logic."""

    def test_utc_to_est(self):
        """20:44 UTC → 15:44 EST."""
        utc_dt = datetime(2026, 1, 15, 20, 44, tzinfo=timezone.utc)
        et = _to_et(utc_dt)
        assert et.hour == 15
        assert et.minute == 44

    def test_utc_to_edt(self):
        """19:44 UTC → 15:44 EDT."""
        utc_dt = datetime(2026, 6, 17, 19, 44, tzinfo=timezone.utc)
        et = _to_et(utc_dt)
        assert et.hour == 15
        assert et.minute == 44

    def test_naive_treated_as_utc(self):
        """Naive datetime should be treated as UTC."""
        naive = datetime(2026, 1, 15, 20, 44)
        et = _to_et(naive)
        assert et.hour == 15
        assert et.minute == 44
