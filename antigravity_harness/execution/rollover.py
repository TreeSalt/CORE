"""
antigravity_harness/execution/rollover.py
=========================================
MES futures rollover enforcement.

Rejects order submission when a contract is within MIN_DAYS_TO_EXPIRY of expiry.
Provides front-month selection logic for research DataTape population.

MES expiry schedule: 3rd Friday of March, June, September, December.
Symbols: MESM26 (June 2026), MESU26 (Sep 2026), MESZ26 (Dec 2026), MESH27 (Mar 2027), etc.
Month codes: H=Mar, M=Jun, U=Sep, Z=Dec

Does NOT: contain strategy logic, broker calls, or live data.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional


# MES quarterly expiry month codes
QUARTERLY_MONTHS = {
    3: "H",   # March
    6: "M",   # June
    9: "U",   # September
    12: "Z",  # December
}

MIN_DAYS_TO_EXPIRY = 2  # From MES constants (mirrors instruments/mes.py)


# ─── Expiry Calculation ───────────────────────────────────────────────────────


def third_friday(year: int, month: int) -> date:
    """Return the 3rd Friday of a given year/month (MES expiry date)."""
    # Find first day of month
    first = date(year, month, 1)
    # Find first Friday
    days_to_friday = (4 - first.weekday()) % 7  # Friday = weekday 4
    first_friday = first + timedelta(days=days_to_friday)
    # Add 2 more weeks
    return first_friday + timedelta(weeks=2)


def get_expiry_date(symbol: str) -> Optional[date]:
    """
    Parse expiry date from a MES futures symbol.

    Supports formats:
        MESM26   → June 2026
        MES      → returns None (continuous contract, no expiry)
        @MES     → returns None (continuous contract)

    Returns None for continuous contracts.
    Raises ValueError for unrecognised symbols.
    """
    # Continuous contract or generic symbol
    if symbol in ("MES", "@MES", "ES", "@ES"):
        return None

    # Parse MESM26 style
    if len(symbol) >= 5 and symbol.startswith("MES"):
        month_code = symbol[3]
        year_part = symbol[4:]
        if len(year_part) == 2:
            year = 2000 + int(year_part)
        elif len(year_part) == 4:
            year = int(year_part)
        else:
            raise ValueError(f"Cannot parse year from symbol: {symbol}")

        month = next(
            (m for m, code in QUARTERLY_MONTHS.items() if code == month_code),
            None,
        )
        if month is None:
            raise ValueError(f"Unrecognised month code '{month_code}' in symbol: {symbol}")

        return third_friday(year, month)

    raise ValueError(f"Cannot determine expiry for symbol: {symbol}")


# ─── Rollover Guard ───────────────────────────────────────────────────────────


@dataclass(frozen=True)
class RolloverGuard:
    """
    Enforces the rule: reject orders within MIN_DAYS_TO_EXPIRY of contract expiry.
    Used by ExecutionSafety before order submission.
    """
    min_days_to_expiry: int = MIN_DAYS_TO_EXPIRY

    def check(self, symbol: str, today: date) -> None:
        """
        Raise RolloverError if symbol is within min_days_to_expiry of expiry.
        Silent (returns None) if safe to trade.
        """
        expiry = get_expiry_date(symbol)
        if expiry is None:
            return  # Continuous contract — no expiry concern

        days_remaining = (expiry - today).days
        if days_remaining < self.min_days_to_expiry:
            raise RolloverError(
                f"ROLLOVER BLOCK: {symbol} expires {expiry} "
                f"({days_remaining} days away, minimum is {self.min_days_to_expiry}). "
                f"Roll to next contract before trading."
            )


class RolloverError(RuntimeError):
    """Raised when an order is rejected due to imminent contract expiry."""
    pass


# ─── Front-Month Selection ────────────────────────────────────────────────────


def front_month_symbol(as_of: date, prefix: str = "MES", days_before_roll: int = 5) -> str:
    """
    Return the front-month symbol for research DataTape population.

    Rolls to the next contract `days_before_roll` calendar days before expiry
    to mirror typical market liquidity migration.

    Examples:
        front_month_symbol(date(2026, 3, 10))  → "MESH26"  (Mar 2026)
        front_month_symbol(date(2026, 3, 16))  → "MESM26"  (Jun 2026, 5 days before Mar expiry)
    """
    # Find the next 4 quarterly expiries from `as_of`
    candidates = []
    year = as_of.year
    for extra_year in range(2):  # Look 2 years out
        for month in sorted(QUARTERLY_MONTHS.keys()):
            exp = third_friday(year + extra_year, month)
            if exp >= as_of:
                candidates.append(exp)

    # Select the nearest contract that is still > days_before_roll away
    for expiry in candidates:
        days_remaining = (expiry - as_of).days
        if days_remaining >= days_before_roll:
            month_code = QUARTERLY_MONTHS[expiry.month]
            year_suffix = str(expiry.year)[2:]
            return f"{prefix}{month_code}{year_suffix}"

    raise ValueError(f"Could not determine front month for {as_of}")


def roll_calendar(
    start: date,
    end: date,
    prefix: str = "MES",
    days_before_roll: int = 5,
) -> list:
    """
    Generate a list of (date, symbol) pairs for the full research window.
    Used when building a DataTape to know which contract to pull for each date.

    Returns list of (date, symbol) tuples where symbol changes on roll dates.
    """
    result = []
    current = start
    while current <= end:
        symbol = front_month_symbol(current, prefix=prefix, days_before_roll=days_before_roll)
        result.append((current, symbol))
        current += timedelta(days=1)
    return result
