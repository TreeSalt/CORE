"""
antigravity_harness/instruments/spy.py
======================================
Single source of truth for SPY (SPDR S&P 500 ETF Trust) instrument physics.

Mirrors the structure of mes.py for fractional equity execution via
Robinhood or other fractional-share brokers.

Does NOT: contain strategy logic, broker calls, or live data.
"""
from __future__ import annotations

from dataclasses import dataclass

from mantis_core.instruments.base import InstrumentSpec

# ─── Core Instrument Physics ─────────────────────────────────────────────────

SPY_TICK_SIZE: float = 0.01
"""Minimum price increment in USD (penny-quoted equity)."""

SPY_MULTIPLIER: float = 1.0
"""USD per share. Equities are 1:1 — no leverage multiplier."""

SPY_LOT_SIZE: float = 0.001
"""Minimum fractional share size (Robinhood supports ~0.001 shares)."""

SPY_EXCHANGE: str = "ARCA"
SPY_CURRENCY: str = "USD"
SPY_SYMBOL: str = "SPY"

# ─── Operator Risk Math (resolved, frozen) ───────────────────────────────────

SPY_CASH_LIMIT_USD: float = 2000.00
"""Hard ceiling on total capital deployed in SPY at any time."""

SPY_MAX_POSITION_USD: float = 2000.00
"""Maximum single-position notional value."""

SPY_STOP_PERCENT: float = 0.5
"""Default stop-loss distance as percentage of entry price."""

SPY_DAILY_LOSS_CAP_USD: float = 50.00
"""Two consecutive losses at max size triggers pause-trading mode."""

SPY_SLIPPAGE_BPS: int = 5
"""Expected slippage in basis points for market orders."""

# ─── Session Boundaries ──────────────────────────────────────────────────────

SPY_SESSION_OPEN_ET: str = "09:30"
SPY_SESSION_CLOSE_ET: str = "16:00"
SPY_NO_NEW_POSITIONS_AFTER_ET: str = "15:50"
SPY_FLATTEN_BY_ET: str = "15:55"
"""All positions must be flat by 15:55 ET. Overnight holds require explicit
operator opt-in via the profile YAML."""

# ─── Derived Helpers ─────────────────────────────────────────────────────────


def shares_from_usd(usd: float, price: float) -> float:
    """Calculate number of fractional shares for a given USD amount."""
    if price <= 0:
        raise ValueError("price must be positive")
    return usd / price


def usd_from_shares(shares: float, price: float) -> float:
    """Calculate USD notional for a given share count."""
    return shares * price


@dataclass(frozen=True)
class SPYRiskParams:
    """
    Resolved, frozen risk parameters for a single SPY trade.
    Use this to pass risk context between safety layer and strategy layer.
    """
    cash_limit_usd: float = SPY_CASH_LIMIT_USD
    stop_percent: float = SPY_STOP_PERCENT
    slippage_bps: int = SPY_SLIPPAGE_BPS

    @property
    def stop_risk_usd(self) -> float:
        """Max loss from stop at current cash deployment."""
        return self.cash_limit_usd * (self.stop_percent / 100.0)

    @property
    def slippage_cost_usd(self) -> float:
        """Expected slippage cost on a round-trip."""
        return self.cash_limit_usd * (self.slippage_bps / 10000.0) * 2

    @property
    def total_planned_risk_usd(self) -> float:
        return self.stop_risk_usd + self.slippage_cost_usd

    def validate(self) -> None:
        """Raise if this risk config violates operator hard limits."""
        if self.cash_limit_usd > SPY_MAX_POSITION_USD:
            raise ValueError(
                f"RISK VIOLATION: cash_limit ${self.cash_limit_usd:.2f} "
                f"exceeds hard limit ${SPY_MAX_POSITION_USD:.2f}."
            )


# ─── Canonical Instrument Spec ───────────────────────────────────────────────

SPY_SPEC = InstrumentSpec(
    symbol=SPY_SYMBOL,
    asset_class="equity",
    tick_size=SPY_TICK_SIZE,
    multiplier=SPY_MULTIPLIER,
    lot_size=SPY_LOT_SIZE,
)
