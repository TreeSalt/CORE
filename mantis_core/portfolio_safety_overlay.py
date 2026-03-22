"""
Phase 9D: Fast Safety Overlay — evaluated every bar, not just at rebalance.
Prevents catastrophic drawdowns by forcing risk-off/risk-reduce between rebalances.
All decisions use t-1 data (no lookahead).
"""

from __future__ import annotations

from enum import Enum
from typing import Dict, List

import pandas as pd
from pydantic import BaseModel, ConfigDict, Field

from mantis_core.regimes import RegimeConfig, RegimeLabel, detect_regime

# ─── Configuration ────────────────────────────────────────────────────────────


class SafetyConfig(BaseModel):
    """All safety overlay thresholds — param-driven, no gate changes."""

    model_config = ConfigDict(frozen=True)

    # Portfolio DD Brake
    dd_reduce: float = -0.15  # DD threshold → RISK_REDUCE
    dd_off: float = -0.25  # DD threshold → RISK_OFF
    dd_hard: float = -0.40  # DD threshold → HARD_FAIL_TRIGGER
    reduce_multiplier: float = 0.5  # Scale weights by this in RISK_REDUCE

    # Re-entry hysteresis (prevents thrashing)
    reentry_off: float = -0.20  # Legacy Hysteresis parameter
    reentry_reduce: float = -0.10  # Legacy Hysteresis parameter

    # Phase 9E Recovery Logic
    reentry_off_to_reduce: float = -0.10  # RISK_OFF -> RISK_REDUCE
    reentry_reduce_to_normal: float = -0.05  # RISK_REDUCE -> NORMAL

    # Panic-by-Physics (always-on secondary)
    enable_panic_physics: bool = True
    regime_cfg: RegimeConfig = Field(default_factory=RegimeConfig)

    # Shock Trigger (tertiary, opt-in)
    enable_shock: bool = False
    shock_ret_thresh: float = -0.12  # 1-bar basket return threshold
    shock_vol_ratio: float = 2.0  # Vol spike threshold


# ─── State ────────────────────────────────────────────────────────────────────


class SafetyState(str, Enum):
    NORMAL = "NORMAL"
    RISK_REDUCE = "RISK_REDUCE"
    RISK_OFF = "RISK_OFF"
    HARD_FAIL_TRIGGER = "HARD_FAIL_TRIGGER"


# ─── Overlay Engine ───────────────────────────────────────────────────────────


class SafetyOverlay:
    """
    Evaluates safety state at every bar using strictly t-1 data.
    Maintains internal state for hysteresis.
    """

    def __init__(self, cfg: SafetyConfig):
        self.cfg = cfg
        self.state = SafetyState.NORMAL
        self.reason: str = ""

    def evaluate(
        self,
        equity_series: List[float],
        close_prices_df: pd.DataFrame,
        asof_idx: int,
        dates: pd.DatetimeIndex,
    ) -> tuple[SafetyState, str, float, float]:
        """
        Evaluate safety state using data up to index asof_idx (t-1).

        Args:
            equity_series: list of equity values [0..current], we use [:asof_idx]
            close_prices_df: full price DataFrame
            asof_idx: current bar index i — we use data up to i-1
            dates: full date index

        Returns:
            (state, reason, dd_asof, ath_asof)
        """
        if asof_idx < 1:
            return SafetyState.NORMAL, "", 0.0, equity_series[0] if equity_series else 0.0

        # ── 1. Portfolio DD Brake (Primary) ──
        # Use equity values up to index i-1 (t-1 semantics)
        eq_history = equity_series[:asof_idx]  # excludes current bar
        ath_asof = max(eq_history)
        current_eq = eq_history[-1]  # equity at t-1
        dd_asof = (current_eq / ath_asof) - 1.0 if ath_asof > 0 else 0.0

        new_state = SafetyState.NORMAL
        reason = ""

        # Check DD thresholds (strictest first)
        if dd_asof <= self.cfg.dd_hard:
            new_state = SafetyState.HARD_FAIL_TRIGGER
            reason = "PORTFOLIO_DD"
        elif dd_asof <= self.cfg.dd_off:
            new_state = SafetyState.RISK_OFF
            reason = "PORTFOLIO_DD"
        elif dd_asof <= self.cfg.dd_reduce:
            new_state = SafetyState.RISK_REDUCE
            reason = "PORTFOLIO_DD"

        # ── 2. Panic-by-Physics (Secondary, always-on) ──
        if self.cfg.enable_panic_physics and asof_idx >= 2:  # noqa: PLR2004
            asof_ts = dates[asof_idx - 1]
            history_df = close_prices_df.iloc[:asof_idx]  # t-1 data

            if (
                len(history_df) >= self.cfg.regime_cfg.window + 1
                and detect_regime(history_df, asof_ts, self.cfg.regime_cfg).label == RegimeLabel.PANIC
                and new_state not in (SafetyState.HARD_FAIL_TRIGGER,)
            ):
                # PANIC overrides to at least RISK_OFF
                new_state = SafetyState.RISK_OFF
                reason = "PANIC"

        # ── 3. Shock Trigger (Tertiary, opt-in) ──
        if self.cfg.enable_shock and asof_idx >= 2:  # noqa: PLR2004
            # 1-bar basket return at t-1 (scale-invariant: mean of per-asset returns)
            prev_prices = close_prices_df.iloc[asof_idx - 2]
            curr_prices = close_prices_df.iloc[asof_idx - 1]
            asset_returns = (curr_prices / prev_prices) - 1.0
            one_bar_ret = asset_returns.mean()
            if one_bar_ret < self.cfg.shock_ret_thresh and new_state == SafetyState.NORMAL:
                new_state = SafetyState.RISK_OFF
                reason = "SHOCK"

        # ── 4. Hysteresis (prevents thrashing) ──
        new_state = self._apply_hysteresis(new_state, dd_asof)

        self.state = new_state
        self.reason = reason
        return new_state, reason, dd_asof, ath_asof

    def _apply_hysteresis(self, proposed: SafetyState, dd_asof: float) -> SafetyState:  # noqa: PLR0911
        """
        Prevent flapping: once in a risk state, require DD recovery past
        a separate (less aggressive) threshold before returning to NORMAL.
        Key rule: never downgrade severity (RISK_OFF → RISK_REDUCE forbidden).
        """
        # If currently in RISK_OFF or HARD_FAIL
        if self.state in (SafetyState.RISK_OFF, SafetyState.HARD_FAIL_TRIGGER):
            # Allow escalation (RISK_OFF → HARD_FAIL)
            if proposed == SafetyState.HARD_FAIL_TRIGGER:
                return proposed

            # Phase 9E: Controlled Recovery
            # RISK_OFF -> RISK_REDUCE if DD >= -0.10 (reentry_off_to_reduce)
            # But ONLY if proposed allows it (e.g. proposed is RISK_OFF, RISK_REDUCE or NORMAL)
            # If proposed is HARD_FAIL, we escalated (handled above).

            # Use strict t-1 DD
            if dd_asof >= self.cfg.reentry_off_to_reduce:
                # We qualify for at least RISK_REDUCE.
                # Check if we qualify for NORMAL too?
                if dd_asof >= self.cfg.reentry_reduce_to_normal:
                    return SafetyState.NORMAL
                return SafetyState.RISK_REDUCE

            # Otherwise stay in RISK_OFF
            return self.state

        # If currently in RISK_REDUCE
        if self.state == SafetyState.RISK_REDUCE:
            # Allow escalation
            if proposed in (SafetyState.RISK_OFF, SafetyState.HARD_FAIL_TRIGGER):
                return proposed

            # Recovery to NORMAL only if DD >= -0.05
            if dd_asof >= self.cfg.reentry_reduce_to_normal:
                return SafetyState.NORMAL

            # Stay reduced
            return SafetyState.RISK_REDUCE

        return proposed

    def apply_to_weights(
        self,
        target_weights: Dict[str, float],
        state: SafetyState,
    ) -> Dict[str, float]:
        """Apply safety state to target weights."""
        if state in (SafetyState.RISK_OFF, SafetyState.HARD_FAIL_TRIGGER):
            return {k: 0.0 for k in target_weights}
        elif state == SafetyState.RISK_REDUCE:
            return {k: v * self.cfg.reduce_multiplier for k, v in target_weights.items()}
        return target_weights
