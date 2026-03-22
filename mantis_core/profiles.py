from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict


class AssetClass(Enum):
    CRYPTO = "CRYPTO"
    EQUITIES = "EQUITIES"


@dataclass(frozen=True)
class AssetProfile:
    name: str
    asset_class: AssetClass
    version: str = "1.0.0"

    # Profit Gates (FAIL only)
    min_pf_profit: float = 1.0
    min_sharpe_profit: float = 0.0
    min_trades_window: int = 30

    # Safety Gates (PASS/WARN/FAIL)
    # WARN band: if metric is between warn_threshold and fail_threshold -> WARN
    # FAIL band: if metric is beyond fail_threshold -> FAIL

    max_dd_warn: float = 0.15
    max_dd_fail: float = 0.25

    # Misclassification Defense
    min_vol_annual: float = 0.0  # If asset vol < this, it's not crypto -> FAIL

    # Execution
    slippage_bps: float = 10.0  # 0.1% default


# CENTRALIZED PROFILE REGISTRY (Versioned)
PROFILES: Dict[str, AssetProfile] = {
    # 1. Equity Fortress (Strict Safety)
    # - Low Volatility needed (no min vol, but max DD strict)
    # - DD > 15% = WARN, DD > 20% = FAIL
    "equity_fortress": AssetProfile(
        name="equity_fortress",
        asset_class=AssetClass.EQUITIES,
        version="6E.1",
        min_pf_profit=1.1,
        min_sharpe_profit=0.5,
        min_trades_window=40,
        max_dd_warn=0.15,
        max_dd_fail=0.20,
        min_vol_annual=0.0,
        slippage_bps=5.0,
    ),
    # 2. Crypto Profit (Growth First)
    # - Explicitly allows higher DD (WARN 25-40%, FAIL >= 40%)
    # - Requires High Vol (min_vol_annual=0.40) to prevent mislabeling boring assets
    "crypto_profit": AssetProfile(
        name="crypto_profit",
        asset_class=AssetClass.CRYPTO,
        version="6E.1",
        min_pf_profit=1.6,
        min_sharpe_profit=0.0,  # PF is king here
        min_trades_window=40,
        max_dd_warn=0.25,  # Traditional limit is now WARN start
        max_dd_fail=0.40,  # Hard Fail
        min_vol_annual=0.40,
        slippage_bps=10.0,
    ),
}


def get_profile(name: str) -> AssetProfile:
    if name not in PROFILES:
        raise ValueError(f"Unknown Profile: {name}. Available: {list(PROFILES.keys())}")
    return PROFILES[name]
