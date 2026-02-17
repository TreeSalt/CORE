"""
antigravity_harness/calendar/cme_calendar.py
============================================
Concrete CalendarAdapter for CME Equity Futures (RTH).

Enforces:
  - RTH Session: 09:30–16:00 America/New_York
  - Strict **15:45 ET** cutoff for new positions (15 mins before close)
  - Hard flatten by **15:55 ET** (5 mins before close)
  - Dynamic handling of holidays/early closes when pandas_market_calendars is available
  - Naive Mon–Fri fallback (no holidays) for minimal verify environments

Note: CME equity futures trade nearly 24h on Globex, but TRADER_OPS operates RTH only.
"""

from __future__ import annotations

import zoneinfo
from datetime import date, datetime, time, timedelta, timezone
from typing import Optional

from antigravity_harness.execution.adapter_base import CalendarAdapter
from antigravity_harness.instruments.mes import (
    MES_SESSION_CLOSE_ET,
    MES_SESSION_OPEN_ET,
)

TZ_ET = zoneinfo.ZoneInfo("America/New_York")

try:
    import pandas_market_calendars as mcal  # type: ignore
    _HAS_MCAL = True
except Exception:  # pragma: no cover
    mcal = None
    _HAS_MCAL = False


def _parse_hhmm(hhmm: str) -> time:
    # Accept "HH:MM" or "HH:MM:SS"
    parts = [int(p) for p in hhmm.split(":")]
    if len(parts) == 2:
        return time(parts[0], parts[1])
    if len(parts) == 3:
        return time(parts[0], parts[1], parts[2])
    raise ValueError(f"Invalid time string: {hhmm!r}")


RTH_OPEN_ET = _parse_hhmm(MES_SESSION_OPEN_ET)   # 09:30
RTH_CLOSE_ET = _parse_hhmm(MES_SESSION_CLOSE_ET) # 16:00


class CMERTHCalendar(CalendarAdapter):
    """CME Equity Futures Regular Trading Hours (RTH) calendar."""

    def __init__(self) -> None:
        self._cal = None
        if _HAS_MCAL:
            # pandas_market_calendars naming varies by version; try a small set.
            for name in ("CME", "CME_Equity", "CME_EQUITY", "CMEGlobexEquity", "CME_GLOBEX_EQUITY"):
                try:
                    self._cal = mcal.get_calendar(name)  # type: ignore[attr-defined]
                    break
                except Exception:
                    self._cal = None

    def is_trading_day(self, d: date) -> bool:
        if d.weekday() >= 5:  # Sat/Sun
            return False
        if self._cal is None:
            return True
        try:
            sched = self._cal.schedule(start_date=d, end_date=d)  # type: ignore[union-attr]
            return not sched.empty
        except Exception:
            # If calendar lookup fails, degrade to naive weekdays.
            return True

    def _effective_close_et(self, d: date) -> Optional[time]:
        """Return close time in ET (handles early close if calendar provides it)."""
        if not self.is_trading_day(d):
            return None

        if self._cal is None:
            return RTH_CLOSE_ET

        try:
            sched = self._cal.schedule(start_date=d, end_date=d)  # type: ignore[union-attr]
            if sched.empty:
                return None
            row = sched.iloc[0]
            market_close_utc = row.get("market_close")
            if market_close_utc is None:
                return RTH_CLOSE_ET

            close_dt_et = market_close_utc.to_pydatetime().astimezone(TZ_ET)
            # If calendar reports a close earlier than 16:00 ET, treat as early close.
            return close_dt_et.time() if close_dt_et.time() < RTH_CLOSE_ET else RTH_CLOSE_ET
        except Exception:
            return RTH_CLOSE_ET

    def session_open_utc(self, d: date) -> Optional[datetime]:
        if not self.is_trading_day(d):
            return None
        dt_et = datetime.combine(d, RTH_OPEN_ET).replace(tzinfo=TZ_ET)
        return dt_et.astimezone(timezone.utc)

    def session_close_utc(self, d: date) -> Optional[datetime]:
        close_et = self._effective_close_et(d)
        if close_et is None:
            return None
        dt_et = datetime.combine(d, close_et).replace(tzinfo=TZ_ET)
        return dt_et.astimezone(timezone.utc)

    def is_early_close(self, d: date) -> bool:
        close_et = self._effective_close_et(d)
        return close_et is not None and close_et < RTH_CLOSE_ET

    def next_trading_day(self, d: date) -> date:
        nxt = d + timedelta(days=1)
        while not self.is_trading_day(nxt):
            nxt += timedelta(days=1)
        return nxt

    # ─── STRICT OVERRIDES ──────────────────────────────────────────────────

    def no_new_positions_time_utc(self, d: date) -> Optional[datetime]:
        """Strict 15-minute buffer: close - 15 minutes."""
        close = self.session_close_utc(d)
        return None if close is None else close - timedelta(minutes=15)

    def flatten_by_utc(self, d: date) -> Optional[datetime]:
        """Hard flatten deadline: close - 5 minutes."""
        close = self.session_close_utc(d)
        return None if close is None else close - timedelta(minutes=5)
