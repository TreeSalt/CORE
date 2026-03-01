import json
from pathlib import Path
from typing import Dict, Optional

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

# MISSION v4.5.370: Capability-aware destination tagging
_CAPABILITY_SNAPSHOT_PATH = None  # Set externally or discovered at runtime


class PortfolioRouter:
    def __init__(
        self, regime_cfg: Optional[RegimeConfig] = None, policy_cfg: Optional[PolicyConfig] = None, interval: str = "1d"
    ):
        self.regime_cfg = regime_cfg or RegimeConfig()
        self.policy_cfg = policy_cfg or PolicyConfig()

        # MISSION v4.5.370: Load CAPABILITY_SNAPSHOT for destination broker tagging
        self.capability_snapshot: dict = {}
        self._load_capability_snapshot()

        # Phase 10.2: Physics Hardening (Annualization Footgun)
        inferred_periods = infer_periods_per_year(interval, is_crypto=self.policy_cfg.is_crypto)

        if self.policy_cfg.periods_per_year == 365 and inferred_periods != 365:  # noqa: PLR2004
            print(f"🔧 PortfolioRouter: Overriding periods_per_year {self.policy_cfg.periods_per_year} -> {inferred_periods} (derived from {interval})")
            self.policy_cfg = self.policy_cfg.model_copy(update={"periods_per_year": inferred_periods})
        elif self.policy_cfg.periods_per_year != inferred_periods:
            print(f"🔧 PortfolioRouter: Enforcing interval physics. {self.policy_cfg.periods_per_year} -> {inferred_periods} (derived from {interval})")
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

    def _load_capability_snapshot(self) -> None:
        """MISSION v4.5.370: Load CAPABILITY_SNAPSHOT.json for destination broker tagging."""
        # Try well-known locations
        candidates = [
            Path(_CAPABILITY_SNAPSHOT_PATH) if _CAPABILITY_SNAPSHOT_PATH else None,
            Path(__file__).resolve().parent.parent / "reports" / "forge" / "ibkr_smoke" / "CAPABILITY_SNAPSHOT.json",
        ]
        for candidate in candidates:
            if candidate and candidate.exists():
                try:
                    self.capability_snapshot = json.loads(candidate.read_text())
                except Exception:
                    self.capability_snapshot = {}
                return

    def _resolve_broker(self, asset: str) -> str:
        """
        MISSION v4.5.370: Resolve destination broker for an asset.
        Uses CAPABILITY_SNAPSHOT if available, otherwise defaults to primary_broker.
        """
        if not self.capability_snapshot:
            return "UNKNOWN"

        primary = self.capability_snapshot.get("primary_broker", "UNKNOWN")
        brokers = self.capability_snapshot.get("brokers", {})

        asset_upper = asset.upper()

        # Futures
        if asset_upper in ("MES", "ES", "NQ", "RTY", "YM", "CL", "GC", "SI"):
            for broker_name, broker_cfg in brokers.items():
                if broker_cfg.get("supports", {}).get("futures", False):
                    return broker_name

        # Crypto
        if asset_upper in ("BTC", "ETH", "SOL", "BTC-USD", "ETH-USD"):
            for broker_name, broker_cfg in brokers.items():
                if broker_cfg.get("supports", {}).get("crypto", False):
                    return broker_name

        # ETFs and Equities
        for broker_name, broker_cfg in brokers.items():
            if broker_cfg.get("supports", {}).get("equities", False):
                return broker_name

        return primary

    def preload(self, close_df: pd.DataFrame) -> None:
        """Vectorized preload of all regimes for the backtest window."""
        metrics = compute_regime_indicators(close_df, self.regime_cfg)
        states = infer_regimes_from_metrics(metrics, self.regime_cfg)
        # MISSION v4.5.380: Bypass mypy/linter friction with direct iteration
        self.preloaded_regimes = {close_df.index[i]: states[i] for i in range(len(states))}

    def route(self, close_df: pd.DataFrame, asof: pd.Timestamp) -> tuple[Dict[str, float], RegimeState]:
        """
        Canonical Router Interface.
        Returns (target_weights, confirmed_regime_state).
        """
        # Resolve Current Regime
        if asof in self.preloaded_regimes:
            raw_state = self.preloaded_regimes[asof]
        else:
            raw_state = detect_regime(close_df, asof, self.regime_cfg, self.last_raw_label)

        self.last_raw_label = raw_state.label
        regime = self.persistence.update(raw_state)

        # ── 1. Active Policy Selection ──
        active_policy: PortfolioPolicy = self.cash_policy
        policy_name = "DefensiveCash"
        
        if RegimeFlag.PANIC in regime.flags or regime.label == RegimeLabel.PANIC:
             active_policy = self.cash_policy
             policy_name = "DefensiveCash"
        elif regime.label in (RegimeLabel.TREND_LOW_VOL, RegimeLabel.TREND_HIGH_VOL):
             active_policy = self.mom_policy
             policy_name = "CrossSectionMomentum"
        elif regime.label in (RegimeLabel.RANGE_LOW_VOL, RegimeLabel.RANGE_HIGH_VOL):
             # Vanguard Effective uses Mean Reversion for Range regimes
             active_policy = self.mr_policy
             policy_name = "CrossSectionMeanReversion"
        else:
             active_policy = self.cash_policy
             policy_name = "DefensiveCash"

        # Record chosen policy in metrics for audit/tests
        regime.metrics["chosen_policy"] = policy_name

        # ── 2. Weight Computation ──
        raw_weights = active_policy.compute_target_weights(close_df, asof, self.policy_cfg)

        # ── 3. Guardrails & Refinement ──
        # Concentration Caps
        final_weights = apply_concentration_caps(raw_weights, self.policy_cfg)

        # Correlation Guard (Vanguard Effective)
        returns = close_df.pct_change(fill_method=None).loc[:asof].iloc[-self.policy_cfg.signal_lookback_bars:]
        kept = CorrelationGuard.filter(returns, threshold=self.regime_cfg.corr_spike_threshold)
        final_weights = {k: v if k in kept else 0.0 for k, v in final_weights.items()}

        # MISSION v4.5.370: Tag regime metrics with destination_broker
        for asset in final_weights:
            if final_weights[asset] != 0:
                broker = self._resolve_broker(asset)
                regime.metrics[f"destination_{asset}"] = broker
                
                # MISSION v4.5.422: Short-Weight Cash Gate
                if final_weights[asset] < 0 and self.capability_snapshot.get("brokers", {}).get(broker, {}).get("account_type") == "cash":
                    print(f"⚠️ PHYSICS VIOLATION: Shorting {asset} blocked on {broker} (CASH ACCOUNT).")
                    final_weights[asset] = 0.0
                    regime.metrics[f"violation_{asset}"] = "CANNOT_SHORT_CASH_ACCOUNT"

        return final_weights, regime
