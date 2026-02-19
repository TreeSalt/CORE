from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set

import numpy as np
import pandas as pd
from pydantic import BaseModel, ConfigDict


# ─── Constants ───
class RegimeLabel(str, Enum):
    TREND_LOW_VOL = "TREND_LOW_VOL"
    TREND_HIGH_VOL = "TREND_HIGH_VOL"
    RANGE_LOW_VOL = "RANGE_LOW_VOL"
    RANGE_HIGH_VOL = "RANGE_HIGH_VOL"
    PANIC = "PANIC"  # Only if panic flags override
    UNKNOWN = "UNKNOWN"  # Vanguard Effective: warmup / insufficient data


class RegimeFlag(str, Enum):
    PANIC = "PANIC"
    CORR_SPIKE = "CORR_SPIKE"
    DISPERSION_HIGH = "DISPERSION_HIGH"
    DISPERSION_LOW = "DISPERSION_LOW"


class RegimeConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    window: int = 24
    # Schmitt Triggers (Hysteresis)
    trend_th_entry: float = 0.6  # Enter TREND if z > 0.6
    trend_th_exit: float = 0.3  # Exit TREND if z < 0.3

    vol_th_entry: float = 1.3  # Enter HIGH_VOL if ratio > 1.3
    vol_th_exit: float = 1.1  # Exit HIGH_VOL if ratio < 1.1

    panic_drawdown: float = -0.15
    panic_drawdown_extreme: float = -0.225  # Phase 10: was hidden `panic_drawdown * 1.5`
    panic_vol_spike: float = 2.0

    # Correlation spike detection (Vanguard Effective: z-score based)
    corr_spike_threshold: float = 0.7  # Legacy fallback (only if < corr_lookback bars)
    corr_lookback: int = 60  # Rolling window for baseline correlation
    corr_z_threshold: float = 2.0  # Z-score threshold for spike detection

    # Legacy compat (will be ignored if Schmitt logic used)
    trend_threshold: float = 0.5
    vol_ratio_threshold: float = 1.2


@dataclass
class RegimeState:
    label: RegimeLabel
    flags: Set[RegimeFlag] = field(default_factory=set)
    metrics: Dict[str, float] = field(default_factory=dict)


def calculate_basket_returns(close_df: pd.DataFrame) -> pd.Series:
    """Calculate equal-weighted basket returns."""
    returns = close_df.pct_change().fillna(0)
    return returns.mean(axis=1)


def detect_regime(  # noqa: PLR0912, PLR0915
    close_df: pd.DataFrame, asof: pd.Timestamp, cfg: RegimeConfig, previous_label: Optional[RegimeLabel] = None
) -> RegimeState:
    """
    Detect market regime with Schmitt Trigger hysteresis.
    """
    # Slice data up to asof
    history = close_df.loc[:asof]
    if len(history) < cfg.window + 1:
        return RegimeState(
            RegimeLabel.UNKNOWN,
            metrics={"insufficient_data": True, "status": "insufficient_data"},
        )

    window_closes = history.iloc[-cfg.window - 1 :]
    returns = window_closes.pct_change().dropna()

    # 1. Trend Metric (Scale Invariant Z-Score)
    basket_daily_returns = returns.mean(axis=1)
    mean_ret = basket_daily_returns.mean()
    std_ret = basket_daily_returns.std()

    trend_z = 0.0
    if std_ret > 1e-9:  # noqa: PLR2004
        trend_z = abs(mean_ret) / std_ret
        trend_z *= np.sqrt(len(basket_daily_returns))

    # 2. Volatility Ratio
    long_window = cfg.window * 4
    long_history = close_df.loc[:asof].iloc[-long_window - 1 :]
    long_returns = long_history.pct_change().dropna().mean(axis=1)

    short_vol_window = max(2, cfg.window // 2)
    rolling_vol = long_returns.rolling(window=short_vol_window).std()

    current_vol = rolling_vol.iloc[-1] if not np.isnan(rolling_vol.iloc[-1]) else 0.0
    median_vol = rolling_vol.median()

    vol_ratio = 1.0
    if median_vol > 1e-9:  # noqa: PLR2004
        vol_ratio = current_vol / median_vol

    # 3. Panic Detection (Scale-Invariant Basket Drawdown)
    window_returns = window_closes.pct_change().fillna(0)
    basket_returns = window_returns.mean(axis=1)
    basket_index = (1 + basket_returns).cumprod() * 100.0
    peak = basket_index.max()
    current = basket_index.iloc[-1]
    drawdown = (current / peak) - 1.0 if peak > 0 else 0.0

    flags = set()
    label = RegimeLabel.RANGE_LOW_VOL

    # Panic Logic (Overrides everything)
    if drawdown < cfg.panic_drawdown and vol_ratio > cfg.panic_vol_spike or drawdown < cfg.panic_drawdown_extreme:
        label = RegimeLabel.PANIC
        flags.add(RegimeFlag.PANIC)
    else:
        # Determine Regime State using Schmitt Triggers

        # Check if we were previously in a TREND state
        was_trending = previous_label in (RegimeLabel.TREND_LOW_VOL, RegimeLabel.TREND_HIGH_VOL)
        trend_threshold = cfg.trend_th_exit if was_trending else cfg.trend_th_entry
        is_trending = trend_z > trend_threshold

        # Check if we were previously in HIGH VOL state
        was_high_vol = previous_label in (RegimeLabel.TREND_HIGH_VOL, RegimeLabel.RANGE_HIGH_VOL)
        vol_threshold = cfg.vol_th_exit if was_high_vol else cfg.vol_th_entry
        is_high_vol = vol_ratio > vol_threshold

        if is_trending and is_high_vol:
            label = RegimeLabel.TREND_HIGH_VOL
        elif is_trending and not is_high_vol:
            label = RegimeLabel.TREND_LOW_VOL
        elif not is_trending and is_high_vol:
            label = RegimeLabel.RANGE_HIGH_VOL
        else:
            label = RegimeLabel.RANGE_LOW_VOL

    # 4. Dispersion Ratio (Cross-Sectional)
    # Ratio of current cross-sectional std of returns vs historical median
    # High dispersion = stock picking environment / rotation
    # Low dispersion = correlation / macro driven
    cs_std = returns.std(axis=1)  # Daily cross-sectional std
    current_disp = cs_std.iloc[-1] if not np.isnan(cs_std.iloc[-1]) else 0.0

    # Compare to historical median dispersion
    long_disp_history = close_df.loc[:asof].iloc[-long_window - 1 :].pct_change().dropna().std(axis=1)
    median_disp = long_disp_history.median()

    dispersion_ratio = 1.0
    if median_disp > 1e-9:  # noqa: PLR2004
        dispersion_ratio = current_disp / median_disp

    if dispersion_ratio > 2.0:  # noqa: PLR2004
        flags.add(RegimeFlag.DISPERSION_HIGH)
    elif dispersion_ratio < 0.5:  # noqa: PLR2004
        flags.add(RegimeFlag.DISPERSION_LOW)

    # Correlation Spike Check (Vanguard Effective: z-score change detector)
    corr_matrix = returns.corr()
    upper_tri = corr_matrix.values[np.triu_indices_from(corr_matrix.values, 1)]
    avg_corr = float(upper_tri.mean()) if len(upper_tri) > 0 else 0.0

    # Compute rolling baseline of avg_corr over longer history
    long_corr_window = min(cfg.corr_lookback, len(close_df.loc[:asof]) - 1)
    if long_corr_window >= cfg.window * 2:
        # We have enough history for a rolling z-score
        rolling_corrs = []
        # Optimization: Limit history to lookback window to avoid O(N^2) complexity
        # Use a safe minimum (e.g. 300 or lookback) to preserve behavior for small datasets (tests)
        safe_lookback = max(long_corr_window, 300)
        full_history = close_df.loc[:asof].iloc[-safe_lookback:]
        
        step = max(1, cfg.window // 2)  # Semi-overlapping windows
        for end_idx in range(cfg.window + 1, len(full_history) + 1, step):
            start_idx = max(0, end_idx - cfg.window)
            block = full_history.iloc[start_idx:end_idx]
            block_rets = block.pct_change().dropna()
            if len(block_rets) >= 3 and block_rets.shape[1] >= 2:  # noqa: PLR2004
                cm = block_rets.corr()
                ut = cm.values[np.triu_indices_from(cm.values, 1)]
                rolling_corrs.append(float(ut.mean()))
        if len(rolling_corrs) >= 5:  # noqa: PLR2004
            corr_mean = float(np.mean(rolling_corrs))
            corr_std = float(np.std(rolling_corrs, ddof=1))
            if corr_std > 1e-6:  # noqa: PLR2004
                corr_z = (avg_corr - corr_mean) / corr_std
                if corr_z > cfg.corr_z_threshold:
                    flags.add(RegimeFlag.CORR_SPIKE)
            # else: no variance → no spike possible
        # Fallback to static threshold if insufficient rolling data
        elif avg_corr > cfg.corr_spike_threshold:
            flags.add(RegimeFlag.CORR_SPIKE)
    # Fallback to static threshold for short histories
    elif avg_corr > cfg.corr_spike_threshold:
        flags.add(RegimeFlag.CORR_SPIKE)

    return RegimeState(
        label=label,
        flags=flags,
        metrics={
            "trend_z": trend_z,
            "trend_dir": np.sign(mean_ret) if abs(mean_ret) > 1e-9 else 0.0,  # noqa: PLR2004
            "vol_ratio": vol_ratio,
            "drawdown": drawdown,
            "avg_corr": avg_corr,
            "dispersion_ratio": dispersion_ratio,
        },
    )


@dataclass
class RegimePersistence:
    """
    Stateful filter to prevent regime thrashing.
    Requires N consecutive bars of a new regime to switch confirmed_regime.
    """

    min_bars: int = 3
    history: List[RegimeLabel] = field(default_factory=list)
    confirmed_regime: Optional[RegimeLabel] = None

    def update(self, current_regime: RegimeState) -> RegimeState:
        """
        Update history and return the confirmed regime state.
        The returned state has the CONFIRMED label, but current flags/metrics.

        Vanguard Effective warmup: NO auto-confirm on first bar.
        confirmed_regime starts as None → returns UNKNOWN.
        Only confirms after min_bars consecutive identical labels.
        """
        self.history.append(current_regime.label)

        # Trim history
        if len(self.history) > self.min_bars:
            self.history.pop(0)

        # Confirmation gate: N consecutive bars required to confirm ANY regime
        # (No bootstrap — stays UNKNOWN until min_bars consecutive)
        if len(self.history) >= self.min_bars:
            candidate = self.history[-1]
            if all(lbl == candidate for lbl in self.history[-self.min_bars :]):
                self.confirmed_regime = candidate

        # Return composite state: Confirmed Label + Current Data
        confirmed = self.confirmed_regime if self.confirmed_regime is not None else RegimeLabel.UNKNOWN
        return RegimeState(
            label=confirmed,
            flags=current_regime.flags,
            metrics=current_regime.metrics,
        )
