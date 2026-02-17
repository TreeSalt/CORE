"""
antigravity_harness.calendar — Trading Calendar Adapters
=========================================================
Calendar-aware trading session management for institutional
execution. Provides cutoff times, session windows, and
flatten triggers.
"""

from antigravity_harness.calendar.cme_calendar import (
    CalendarAdapter,
    CMERTHCalendar,
)

__all__ = [
    "CalendarAdapter",
    "CMERTHCalendar",
]
