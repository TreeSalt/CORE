from typing import Dict, Optional

import numpy as np
import pandas as pd

from antigravity_harness.correlation import CorrelationGuard
from antigravity_harness.portfolio_policies import (
    CrossSectionMeanReversionPolicy,
    CrossSectionMomentumPolicy,
    DefensiveCashPolicy,
    InverseVolatilityPolicy,
    PolicyConfig,
    PortfolioPolicy,
    apply_concentration_caps,
)
from antigravity_harness.regimes import (
    RegimeConfig,
    RegimeFlag,
    RegimeLabel,
    RegimePersistence,
    RegimeState,
    compute_regime_indicators,
    detect_regime,
    infer_regimes_from_metrics,
)
from antigravity_harness.utils import infer_periods_per_year


class PortfolioRouter:
    def __init__(
        self, regime_cfg: Optional[RegimeConfig] = None, policy_cfg: Optional[PolicyConfig] = None, interval: str = "1d"
    ):
        self.regime_cfg = regime_cfg or RegimeConfig()
        self.policy_cfg = policy_cfg or PolicyConfig()

        # Phase 10.2: Physics Hardening (Annualization Footgun)
        # "Do NOT trust the config default if it conflicts with the interval."
        inferred_periods = infer_periods_per_year(interval, is_crypto=self.policy_cfg.is_crypto)

        # If policy has default 365 but interval implies something else (e.g. 4h -> 2190), override.
        # Or if policy has 365 and interval is 1d, it matches.
        # Ideally we ALWAYS override with the inferred value from the interval context,
        # unless the user explicitly set a custom periods_per_year in config (how do we know?).
        # We assume if it equals 365 (default), we are free to override.
        if self.policy_cfg.periods_per_year == 365 and inferred_periods != 365:  # noqa: PLR2004
            print(
                f"🔧 PortfolioRouter: Overriding periods_per_year {self.policy_cfg.periods_per_year} -> {inferred_periods} (derived from {interval})"  # noqa: E501
            )
            self.policy_cfg = self.policy_cfg.model_copy(update={"periods_per_year": inferred_periods})
        elif self.policy_cfg.periods_per_year != inferred_periods:
            # If config has non-default (e.g. 252) but we are 4h... warn?
            # Prompt says "Do NOT trust the config default".
            # Let's enforce the interval truth.
            print(
                f"🔧 PortfolioRouter: Enforcing interval physics. {self.policy_cfg.periods_per_year} -> {inferred_periods} (derived from {interval})"  # noqa: E501
            )
            self.policy_cfg = self.policy_cfg.model_copy(update={"periods_per_year": inferred_periods})
        else:
            print(f"🔧 PortfolioRouter: Physics verified. periods_per_year={inferred_periods} (matches {interval})")

        # Instantiate policies
        self.cash_policy = DefensiveCashPolicy()
        self.mom_policy = CrossSectionMomentumPolicy()
        self.mr_policy = CrossSectionMeanReversionPolicy()
        self.inv_vol_policy = InverseVolatilityPolicy()

        # Phase 9E: Regime Persistence & Schmitt State
        self.persistence = RegimePersistence(min_bars=3)
        self.last_raw_label: Optional[RegimeLabel] = None

        # Optimization: Preloaded Regimes
        self.preloaded_regimes: Dict[pd.Timestamp, RegimeState] = {}

    def preload(self, close_df: pd.DataFrame) -> None:
        """
        Pre-compute regime states for the entire history using vectorized operations.
        This provides O(N) performance vs O(N^2) of iterative detection.
        """
        print(f"⚡ PortfolioRouter: Preloading regimes for {len(close_df)} bars...")
        metrics = compute_regime_indicators(close_df, self.regime_cfg)
        states = infer_regimes_from_metrics(metrics, self.regime_cfg)

        # Align states with timestamps
        # infer_regimes_from_metrics returns a list of states corresponding to metrics rows
        if len(states) != len(close_df):
            print(f"⚠️ Preload mismatch: {len(states)} states vs {len(close_df)} bars.")
            return

        self.preloaded_regimes = dict(zip(close_df.index, states, strict=True))
        print("⚡ Preload complete.")

    def route(self, close_df: pd.DataFrame, asof: pd.Timestamp) -> tuple:  # noqa: PLR0912, PLR0915
        """
        Determines the regime and routes to the appropriate policy.
        Returns (target_weights, regime_state).
        regime_state.metrics is enriched with chosen_policy, vol_scalar, realized_vol.
        """
        # 1. Detect Regime (Raw) with Schmitt Hysteresis
        # Fast Path: Check preload
        if asof in self.preloaded_regimes:
            raw_regime = self.preloaded_regimes[asof]
        else:
            # Slow Path: Legacy / Online
            raw_regime = detect_regime(close_df, asof, self.regime_cfg, previous_label=self.last_raw_label)

        self.last_raw_label = raw_regime.label

        # 1b. Apply Persistence (Time Hysteresis)
        regime = self.persistence.update(raw_regime)

        # 2. Select Policy
        chosen_policy: PortfolioPolicy = self.cash_policy
        chosen_policy_name = "DefensiveCash"
        risk_scale = 1.0

        # Vanguard Effective: UNKNOWN (warmup / insufficient data) → always Cash
        if regime.label == RegimeLabel.UNKNOWN:
            chosen_policy = self.cash_policy
            chosen_policy_name = "DefensiveCash"
        elif RegimeFlag.PANIC in regime.flags or regime.label == RegimeLabel.PANIC:
            # Phase III: Inverse Alpha Extraction (Opt-in)
            if self.policy_cfg.enable_inverse_hedging:
                chosen_policy = self.inv_vol_policy
                chosen_policy_name = "InverseVolatilityHedging"
                risk_scale = 1.0  # Full hedge in panic
            else:
                chosen_policy = self.cash_policy
                chosen_policy_name = "DefensiveCash"
        elif regime.label == RegimeLabel.TREND_LOW_VOL:
            # Phase 9F: Direction Check (Long Only)
            trend_dir = regime.metrics.get("trend_dir", 0)
            if trend_dir > 0:
                chosen_policy = self.mom_policy
                chosen_policy_name = "CrossSectionMomentum"
            else:
                chosen_policy = self.cash_policy
                chosen_policy_name = "DefensiveCash"
        elif regime.label == RegimeLabel.TREND_HIGH_VOL:
            # Phase 9F: Direction Check
            trend_dir = regime.metrics.get("trend_dir", 0)
            if trend_dir > 0:
                chosen_policy = self.mom_policy
                chosen_policy_name = "CrossSectionMomentum"
                risk_scale = 0.5  # Reduce exposure in high vol trend
            else:
                chosen_policy = self.cash_policy
                chosen_policy_name = "DefensiveCash"
        elif regime.label == RegimeLabel.RANGE_LOW_VOL:
            chosen_policy = self.mr_policy
            chosen_policy_name = "CrossSectionMeanReversion"
        elif regime.label == RegimeLabel.RANGE_HIGH_VOL:
            chosen_policy = self.cash_policy
            chosen_policy_name = "DefensiveCash"
        else:
            chosen_policy = self.cash_policy
            chosen_policy_name = "DefensiveCash"

        # 3. Correlation Guard (Surgical Filter)
        if RegimeFlag.CORR_SPIKE in regime.flags and isinstance(
            chosen_policy, (CrossSectionMomentumPolicy, CrossSectionMeanReversionPolicy)
        ):
            # Lookback window for correlation matrix
            corr_window = self.regime_cfg.corr_lookback
            # Get returns for all assets in the universe
            returns_history = close_df.loc[:asof].pct_change(fill_method=None).iloc[-corr_window:]

            # Surgical Filtering: Drop high-volatility assets in correlated pairs
            safe_assets = CorrelationGuard.filter(returns_history, threshold=0.85)

            # Trace dropped assets
            dropped_assets = set(close_df.columns) - set(safe_assets)
            regime.metrics["corr_dropped_count"] = len(dropped_assets)
            if dropped_assets:
                regime.metrics["corr_dropped_list"] = ",".join(sorted(dropped_assets))
        else:
            safe_assets = set(close_df.columns)
            regime.metrics["corr_dropped_count"] = 0

        # 4. Compute Weights
        raw_weights = chosen_policy.compute_target_weights(close_df, asof, self.policy_cfg)

        # Phase 10.4: Fiduciary Hardening (Omega)
        # Enforce per-asset concentration caps from PolicyConfig
        raw_weights = apply_concentration_caps(raw_weights, self.policy_cfg)

        # 5. Apply Risk Scaling & Surgical Filter
        final_weights = {k: v * risk_scale for k, v in raw_weights.items() if k in safe_assets}

        # 6. Vol Targeting (Phase 9F)
        vol_scalar = 1.0
        realized_vol = 0.0
        if self.policy_cfg.target_vol_annual > 0 and sum(final_weights.values()) > 0:
            vol_scalar, realized_vol = self._compute_vol_scalar(close_df, asof, final_weights)
            final_weights = {k: v * vol_scalar for k, v in final_weights.items()}

        # 7. Validate: ensure sum <= max_gross_exposure
        total_weight = sum(final_weights.values())
        max_exp = self.policy_cfg.max_gross_exposure
        if total_weight > max_exp + 1e-6:
            scale_down = max_exp / total_weight
            final_weights = {k: v * scale_down for k, v in final_weights.items()}

        # Enrich regime metrics with router trace data
        regime.metrics["chosen_policy"] = chosen_policy_name
        regime.metrics["risk_scale"] = risk_scale
        regime.metrics["vol_scalar"] = vol_scalar
        regime.metrics["realized_vol_annual"] = realized_vol
        regime.metrics["gross_exposure"] = round(sum(final_weights.values()), 6)

        # Phase 10.3: Unified Physics Export
        regime.metrics["periods_per_year"] = self.policy_cfg.periods_per_year

        return final_weights, regime

    def _compute_vol_scalar(
        self,
        close_df: pd.DataFrame,
        asof: pd.Timestamp,
        weights: Dict[str, float],
    ) -> tuple:
        """
        Compute vol scalar for vol targeting.
        Returns (vol_scalar, realized_vol_annual).
        """
        cfg = self.policy_cfg
        history = close_df.loc[:asof].iloc[-(cfg.vol_lookback + 1) :]
        if len(history) < 5:  # noqa: PLR2004
            return 1.0, 0.0

        returns = history.pct_change().dropna()
        if returns.empty:
            return 1.0, 0.0

        # Weighted portfolio returns
        active_assets = [k for k, v in weights.items() if v > 0 and k in returns.columns]
        if not active_assets:
            return 1.0, 0.0

        w_arr = np.array([weights[a] for a in active_assets])
        r_arr = returns[active_assets].values  # (T, N)
        port_returns = r_arr @ w_arr  # (T,)

        realized_vol_daily = np.std(port_returns, ddof=1)
        realized_vol_annual = realized_vol_daily * np.sqrt(cfg.periods_per_year)

        if realized_vol_annual < 1e-9:  # noqa: PLR2004
            return 1.0, float(realized_vol_annual)

        raw_scalar = cfg.target_vol_annual / realized_vol_annual
        # Clamp: never exceed max_gross_exposure, never go below 0
        clamped = max(0.0, min(raw_scalar, cfg.max_gross_exposure / max(sum(w_arr), 1e-9)))

        return float(clamped), float(realized_vol_annual)
