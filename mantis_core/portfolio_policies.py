from abc import ABC, abstractmethod
from typing import Dict

import numpy as np
import pandas as pd
from pydantic import BaseModel, ConfigDict


class PolicyConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    top_k: int = 3
    signal_lookback_bars: int = 24  # MISSION v4.5.290: Rename lookback
    min_vol: float = 0.001
    max_weight_per_asset: float = 1.0  # MISSION v4.5.291: Override to 1.0 for single-instrument tests
    min_positions: int = 1  # MISSION v4.5.291: Allow single asset deployment
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

    # 1. Clamp (support negative weights for shorts)
    capped = {}
    for k, v in weights.items():
        if v >= 0:
            capped[k] = min(v, cfg.max_weight_per_asset)
        else:
            capped[k] = max(v, -cfg.max_weight_per_asset)

    # 2. Min positions check
    non_zero = [k for k, v in capped.items() if abs(v) > 1e-6]
    if 0 < len(non_zero) < cfg.min_positions:
        # Not enough positions → go to cash (safety)
        return {k: 0.0 for k in weights}

    # 3. Renormalize to original gross total (capping may reduce sum)
    capped_gross = sum(abs(v) for v in capped.values())
    original_gross = sum(abs(v) for v in weights.values())
    
    if capped_gross > 0 and capped_gross < original_gross:
        scale = min(original_gross, cfg.max_gross_exposure) / capped_gross
        renormed = {}
        for k, v in capped.items():
            # Ensure we don't exceed cap after rescaling
            if v >= 0:
                renormed[k] = min(v * scale, cfg.max_weight_per_asset)
            else:
                renormed[k] = max(v * scale, -cfg.max_weight_per_asset)
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
        history = close_df.loc[:asof].iloc[-cfg.signal_lookback_bars - 1 :]
        if len(history) < 2:  # noqa: PLR2004
            return {col: 0.0 for col in close_df.columns}

        # Calculate momentum
        returns = (history.iloc[-1] / history.iloc[0]) - 1.0

        # Rank
        ranked = returns.sort_values(ascending=False)
        top_k = ranked.head(cfg.top_k).index.tolist()

        # momentum logic: Long winners, Short losers
        long_candidates = [sym for sym in top_k if returns[sym] > 0]
        
        # Also handle shorts for bottom_k if enabled? 
        # For simplicity, we'll just allow negative weights if the strategy signal or regime dictates.
        # But this policy is Cross-Sectional. Let's allow Shorting the bottom-k.
        ranked_asc = returns.sort_values(ascending=True)
        bottom_k = ranked_asc.head(cfg.top_k).index.tolist()
        short_candidates = [sym for sym in bottom_k if returns[sym] < 0]

        total_active = len(long_candidates) + len(short_candidates)
        if total_active == 0:
            return {col: 0.0 for col in close_df.columns}

        weight = 1.0 / total_active
        out = {col: 0.0 for col in close_df.columns}
        for sym in long_candidates:
            out[sym] = weight
        for sym in short_candidates:
            out[sym] = -weight
        return out


class CrossSectionMeanReversionPolicy(PortfolioPolicy):
    def compute_target_weights(self, close_df: pd.DataFrame, asof: pd.Timestamp, cfg: PolicyConfig) -> Dict[str, float]:
        """Long Bottom-K assets (Contrarian)."""
        history = close_df.loc[:asof].iloc[-cfg.signal_lookback_bars - 1 :]
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
        history = close_df.loc[:asof].iloc[-cfg.signal_lookback_bars - 1 :]
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
