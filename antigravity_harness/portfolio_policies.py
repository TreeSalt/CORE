from abc import ABC, abstractmethod
from typing import Dict

import numpy as np
import pandas as pd
from pydantic import BaseModel, ConfigDict


class PolicyConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    top_k: int = 3
    lookback: int = 24
    min_vol: float = 0.001
    max_weight_per_asset: float = 0.50  # Phase 9D: per-asset cap
    min_positions: int = 2  # Phase 9D: diversification floor
    crash_floor: float = -0.20  # Phase 9E: falling knife return floor
    target_vol_annual: float = 0.0  # e.g. 0.15 = 15% annual target vol
    max_gross_exposure: float = 1.0  # No leverage by default
    vol_lookback: int = 20  # Bars for realized vol calculation
    periods_per_year: int = 365  # Phase 10: Dynamic annualization
    is_crypto: bool = True  # Phase 10.3: Asset Class Awareness (True=365, False=252)
    enable_inverse_hedging: bool = False  # Phase III: Downturn Mastery


def apply_concentration_caps(
    weights: Dict[str, float],
    cfg: PolicyConfig,
) -> Dict[str, float]:
    """
    Phase 9D: Apply concentration caps to raw policy weights.
    1. Clamp each weight to max_weight_per_asset.
    2. Enforce min_positions (if fewer non-zero weights, go to cash).
    3. Renormalize so weights sum to original total (or less).
    """
    if not weights or all(v == 0.0 for v in weights.values()):
        return weights

    original_total = sum(weights.values())
    if original_total <= 0:
        return weights

    # 1. Clamp
    capped = {k: min(v, cfg.max_weight_per_asset) for k, v in weights.items()}

    # 2. Min positions check
    non_zero = [k for k, v in capped.items() if v > 0]
    if 0 < len(non_zero) < cfg.min_positions:
        # Not enough positions → go to cash (safety)
        return {k: 0.0 for k in weights}

    # 3. Renormalize to original total (capping may reduce sum)
    capped_total = sum(capped.values())
    if capped_total > 0 and capped_total < original_total:
        # Only re-scale up to original_total, never above 1.0
        scale = min(original_total, 1.0) / capped_total
        # But don't let any single weight exceed cap after rescaling
        renormed = {}
        for k, v in capped.items():
            renormed[k] = min(v * scale, cfg.max_weight_per_asset)
        return renormed

    return capped


class PortfolioPolicy(ABC):
    @abstractmethod
    def compute_target_weights(self, close_df: pd.DataFrame, asof: pd.Timestamp, cfg: PolicyConfig) -> Dict[str, float]:
        """Compute target weights for the portfolio. Must sum to <= 1.0."""
        pass


class DefensiveCashPolicy(PortfolioPolicy):
    def compute_target_weights(self, close_df: pd.DataFrame, asof: pd.Timestamp, cfg: PolicyConfig) -> Dict[str, float]:
        # All cash, zero weights
        return {col: 0.0 for col in close_df.columns}


class CrossSectionMomentumPolicy(PortfolioPolicy):
    def compute_target_weights(self, close_df: pd.DataFrame, asof: pd.Timestamp, cfg: PolicyConfig) -> Dict[str, float]:
        """Long Top-K assets by momentum (returns over lookback). Equal weight."""
        # Slice history
        history = close_df.loc[:asof].iloc[-cfg.lookback - 1 :]
        if len(history) < 2:  # noqa: PLR2004
            return {col: 0.0 for col in close_df.columns}

        # Calculate momentum
        returns = (history.iloc[-1] / history.iloc[0]) - 1.0

        # Rank
        ranked = returns.sort_values(ascending=False)
        top_k = ranked.head(cfg.top_k).index.tolist()

        # Check if momentum is positive? Prompt implies "Long-only top-k rotation".
        # Safe to assume we only long positive momentum?
        # Standard CS Mom usually longs top decile regardless.
        # But this is "Long-only". Longing a loser just because it's the "best of losers" is bad.
        # Let's add a filter: Return must be > 0.
        top_k = [sym for sym in top_k if returns[sym] > 0]

        if not top_k:
            return {col: 0.0 for col in close_df.columns}

        weight = 1.0 / len(top_k)
        return {sym: (weight if sym in top_k else 0.0) for sym in close_df.columns}


class CrossSectionMeanReversionPolicy(PortfolioPolicy):
    def compute_target_weights(self, close_df: pd.DataFrame, asof: pd.Timestamp, cfg: PolicyConfig) -> Dict[str, float]:
        """Long Bottom-K assets (Contrarian)."""
        history = close_df.loc[:asof].iloc[-cfg.lookback - 1 :]
        if len(history) < 2:  # noqa: PLR2004
            return {col: 0.0 for col in close_df.columns}

        returns = (history.iloc[-1] / history.iloc[0]) - 1.0

        # Rank ascending (losers first)
        ranked = returns.sort_values(ascending=True)
        bottom_k = ranked.head(cfg.top_k).index.tolist()

        # Filter: Don't catch falling knives AND don't buy positives
        # Vanguard Effective: crash_floor <= return < 0
        # Phase 9E: Crash Guard (Falling Knife)
        # If return is < crash_floor (e.g. -0.20), exclude it.
        # Vanguard: If return >= 0, also exclude (not oversold).
        bottom_k = [sym for sym in bottom_k if cfg.crash_floor <= returns[sym] < 0]

        if not bottom_k:
            # Safety: if no candidates pass the filter, go to cash
            return {col: 0.0 for col in close_df.columns}

        weight = 1.0 / len(bottom_k)
        return {sym: (weight if sym in bottom_k else 0.0) for sym in close_df.columns}


class InverseVolatilityPolicy(PortfolioPolicy):
    def compute_target_weights(self, close_df: pd.DataFrame, asof: pd.Timestamp, cfg: PolicyConfig) -> Dict[str, float]:
        """Weight by 1/Vol."""
        history = close_df.loc[:asof].iloc[-cfg.lookback - 1 :]
        if len(history) < 5:  # noqa: PLR2004
            return {col: 0.0 for col in close_df.columns}

        returns = history.pct_change().dropna()
        vols = returns.std()

        # Handle zero vol or NaN
        vols = vols.replace(0, np.inf)
        inv_vols = 1.0 / vols
        inv_vols = inv_vols.replace([np.inf, -np.inf], 0.0).fillna(0.0)

        total_inv_vol = inv_vols.sum()
        if total_inv_vol == 0:
            return {col: 0.0 for col in close_df.columns}

        weights = inv_vols / total_inv_vol
        return weights.to_dict()
