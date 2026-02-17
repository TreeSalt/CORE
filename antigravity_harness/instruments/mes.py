"""
antigravity_harness/instruments/mes.py
======================================
Single source of truth for Micro E-mini S&P 500 (MES) contract physics.

Every risk calculation, sizing function, and strategy in this system
imports constants from HERE. Never hardcode these values inline.

Does NOT: contain strategy logic, broker calls, or live data.
"""
from __future__ import annotations

from dataclasses import dataclass

# ─── Core Contract Physics ────────────────────────────────────────────────────

MES_POINT_VALUE: float = 5.00
"""USD per index point. 1 full S&P point = $5.00 on MES."""

MES_TICK_SIZE: float = 0.25
"""Minimum price increment in index points."""

MES_TICK_VALUE: float = 1.25
"""USD per tick. MES_POINT_VALUE × MES_TICK_SIZE."""

MES_EXCHANGE: str = "CME"
MES_CURRENCY: str = "USD"
MES_CONTRACT_SYMBOL: str = "MES"
MES_FULL_CONTRACT_SYMBOL: str = "ES"  # Standard E-mini, same underlying

# ─── Operator Risk Math (resolved, frozen) ───────────────────────────────────

MES_STOP_POINTS: float = 7.0
"""Planned stop distance in index points. $35 dollar risk at 1 contract."""

MES_STOP_RISK_USD: float = MES_STOP_POINTS * MES_POINT_VALUE  # $35.00

MES_SLIPPAGE_BUFFER_TICKS: int = 4
"""Reserved slippage buffer in ticks. 4 ticks × $1.25 = $5.00."""

MES_SLIPPAGE_BUFFER_USD: float = MES_SLIPPAGE_BUFFER_TICKS * MES_TICK_VALUE  # $5.00

MES_MAX_PLANNED_RISK_USD: float = MES_STOP_RISK_USD + MES_SLIPPAGE_BUFFER_USD  # $40.00
"""Hard ceiling. planned_stop_risk + buffer_risk must never exceed this."""

MES_DAILY_LOSS_CAP_USD: float = 80.00
"""Two full-risk losses in a day triggers pause-trading mode."""

MES_MAX_CONTRACTS_PHASE1: int = 1
"""Hard ceiling on position size until Stage 3 gates pass."""

# ─── Volatility Filter ────────────────────────────────────────────────────────

MES_DAILY_ATR_NORMAL_LOW: float = 20.0
MES_DAILY_ATR_NORMAL_HIGH: float = 60.0
MES_DAILY_ATR_NO_TRADE: float = 80.0
"""Daily ATR (14-period) above this value: do not initiate new positions.
An 80-point daily range means the session could move $400 against 1 MES —
making an 8-point stop statistically unreliable."""

# ─── Session Boundaries (RTH — Regular Trading Hours) ────────────────────────

MES_SESSION_OPEN_ET: str = "09:30"
MES_SESSION_CLOSE_ET: str = "16:00"
MES_NO_NEW_POSITIONS_AFTER_ET: str = "15:45"
MES_FLATTEN_BY_ET: str = "15:55"
"""All positions must be flat by 15:55 ET. Overnight holds: NEVER."""

# ─── Rollover Safety ─────────────────────────────────────────────────────────

MES_MIN_DAYS_TO_EXPIRY: int = 2
"""Reject orders if contract expiry is fewer than this many calendar days away."""

# ─── Derived Helper ───────────────────────────────────────────────────────────


def points_to_usd(points: float, contracts: int = 1) -> float:
    """Convert index points to USD P&L for MES."""
    return points * MES_POINT_VALUE * contracts


def ticks_to_usd(ticks: int, contracts: int = 1) -> float:
    """Convert ticks to USD P&L for MES."""
    return ticks * MES_TICK_VALUE * contracts


def usd_to_points(usd: float, contracts: int = 1) -> float:
    """Convert USD amount to equivalent index points for MES."""
    if contracts == 0:
        raise ValueError("contracts must be non-zero")
    return usd / (MES_POINT_VALUE * contracts)


@dataclass(frozen=True)
class MESRiskParams:
    """
    Resolved, frozen risk parameters for a single MES trade.
    Use this to pass risk context between safety layer and strategy layer.
    """
    stop_points: float = MES_STOP_POINTS
    slippage_buffer_ticks: int = MES_SLIPPAGE_BUFFER_TICKS
    max_contracts: int = MES_MAX_CONTRACTS_PHASE1

    @property
    def stop_risk_usd(self) -> float:
        return self.stop_points * MES_POINT_VALUE * self.max_contracts

    @property
    def buffer_risk_usd(self) -> float:
        return self.slippage_buffer_ticks * MES_TICK_VALUE * self.max_contracts

    @property
    def total_planned_risk_usd(self) -> float:
        return self.stop_risk_usd + self.buffer_risk_usd

    def validate(self) -> None:
        """Raise if this risk config violates operator hard limits."""
        if self.total_planned_risk_usd > MES_MAX_PLANNED_RISK_USD:
            raise ValueError(
                f"RISK VIOLATION: planned ${self.total_planned_risk_usd:.2f} "
                f"exceeds hard limit ${MES_MAX_PLANNED_RISK_USD:.2f}. "
                f"stop={self.stop_points}pts (${self.stop_risk_usd:.2f}) + "
                f"buffer={self.slippage_buffer_ticks}tks (${self.buffer_risk_usd:.2f})"
            )
