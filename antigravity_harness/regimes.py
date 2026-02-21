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

    # Item 17: ML Classification
    use_ml_classification: bool = False
    ml_clusters: int = 4
    ml_fit_window: int = 252  # Periodic re-fit interval

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


def compute_regime_indicators(  # noqa: PLR0915
    close_df: pd.DataFrame, cfg: RegimeConfig
) -> pd.DataFrame:
    """
    Vectorized calculation of all regime indicators (Trend Z, Vol Ratio, Drawdown, Dispersion).
    Returns a DataFrame aligned with close_df.index containing the metrics.
    """
    # 0. Returns
    daily_returns = close_df.pct_change(fill_method=None).fillna(0.0)

    # 1. Trend Metric (Scale Invariant Z-Score)
    # Basket Return (Equal Weight)
    basket_returns = daily_returns.mean(axis=1)
    rolling_basket = basket_returns.rolling(window=cfg.window, min_periods=cfg.window)
    
    mean_ret = rolling_basket.mean()
    std_ret = rolling_basket.std()
    
    # Avoid div/0 and noise amplification
    # Legacy: if std_ret > 1e-9 ...
    trend_z = np.where(
        std_ret > 1e-9,
        (mean_ret.abs() / std_ret) * np.sqrt(cfg.window),
        0.0
    )
    # Ensure Series alignment
    trend_z = pd.Series(trend_z, index=close_df.index).fillna(0.0)

    # 2. Volatility Ratio
    long_window = cfg.window * 4
    
    # Short-term vol
    short_vol_window = max(2, cfg.window // 2)
    rolling_vol = basket_returns.rolling(window=short_vol_window, min_periods=short_vol_window).std()
    
    # Median Vol (over long window of the short-term vol)
    median_vol = rolling_vol.rolling(window=long_window, min_periods=short_vol_window).median()
    
    # Avoid div/0 and noise
    # Legacy: if median_vol > 1e-9 ...
    vol_ratio = np.where(
        median_vol > 1e-9,
        rolling_vol / median_vol,
        1.0
    )
    vol_ratio = pd.Series(vol_ratio, index=close_df.index).fillna(1.0)

    # 3. Panic Detection (Scale-Invariant Basket Drawdown)
    # Rolling Max of Cumulative Return Index
    basket_idx = (1 + basket_returns).cumprod()
    rolling_peak = basket_idx.rolling(window=cfg.window, min_periods=1).max()
    drawdown = (basket_idx / rolling_peak) - 1.0
    drawdown = drawdown.fillna(0.0)

    # 4. Dispersion Ratio (Cross-Sectional)
    cs_std = daily_returns.std(axis=1)
    rolling_cs_median = cs_std.rolling(window=long_window, min_periods=short_vol_window).median()
    
    dispersion_ratio = np.where(
        rolling_cs_median > 1e-9,
        cs_std / rolling_cs_median,
        1.0
    )
    dispersion_ratio = pd.Series(dispersion_ratio, index=close_df.index).fillna(1.0)
    
    # 5. Trend Direction (Sign of mean return)
    # Use fillna(0) to handle NaN at start
    trend_dir = np.sign(mean_ret).fillna(0.0)
    
    # 6. Average Correlation (O(N) Complexity via Variance of Z-Sums)
    # rho_avg = (Var(Sum(Z_i)) - N) / (N * (N-1))
    roll_mean = daily_returns.rolling(window=cfg.window).mean()
    roll_std = daily_returns.rolling(window=cfg.window).std()
    
    # Standardize returns over the rolling window
    # Avoid div/0 with fillna(0)
    z_returns = ((daily_returns - roll_mean) / roll_std).fillna(0.0)
    sum_z = z_returns.sum(axis=1)
    
    # Variance of the sum of Z-scores (mean is 0 by construction)
    var_sum_z = (sum_z**2).rolling(window=cfg.window).mean()
    num_assets = len(close_df.columns)
    
    if num_assets > 1:
        avg_corr = (var_sum_z - num_assets) / (num_assets * (num_assets - 1))
        avg_corr = avg_corr.clip(0.0, 1.0)
    else:
        avg_corr = pd.Series(0.0, index=close_df.index)
    
    # 7. Correlation Spike (Z-Score of avg_corr)
    # We use a longer window (corr_lookback) for the baseline
    corr_lookback = cfg.corr_lookback
    roll_corr_mean = avg_corr.rolling(window=corr_lookback, min_periods=cfg.window).mean()
    roll_corr_std = avg_corr.rolling(window=corr_lookback, min_periods=cfg.window).std()
    
    corr_z = ((avg_corr - roll_corr_mean) / roll_corr_std).fillna(0.0)

    # Combine into DataFrame
    metrics = pd.DataFrame({
        "trend_z": trend_z,
        "vol_ratio": vol_ratio,
        "drawdown": drawdown,
        "dispersion_ratio": dispersion_ratio,
        "trend_dir": trend_dir,
        "avg_corr": avg_corr,
        "corr_z": corr_z,
        "realized_vol_annual": rolling_vol * np.sqrt(252), # Approx annual vol
    }, index=close_df.index)
    
    return metrics


def infer_regimes_from_metrics(
    metrics_df: pd.DataFrame, cfg: RegimeConfig
) -> List[RegimeState]:
    """
    Apply Schmitt Trigger or ML Clustering iteratively over pre-computed metrics.
    Fast O(N) loop (just logic, no heavy math) for Schmitt.
    """
    if getattr(cfg, "use_ml_classification", False):
        return _infer_ml_regimes(metrics_df, cfg)
        
    states = []
    
    # Schmitt Hysteresis State
    was_trending = False
    was_high_vol = False
    
    # Pre-fetch numpy arrays for raw speed
    n = len(metrics_df)
    trend_z = metrics_df["trend_z"].values
    vol_ratio = metrics_df["vol_ratio"].values
    drawdown = metrics_df["drawdown"].values
    disp_ratio = metrics_df["dispersion_ratio"].values
    trend_dir = metrics_df["trend_dir"].values
    avg_corr = metrics_df["avg_corr"].values
    corr_z = metrics_df["corr_z"].values
    real_vol = metrics_df["realized_vol_annual"].values
    
    for i in range(n):
        # Warmup Guard
        if i < cfg.window:
            states.append(RegimeState(RegimeLabel.UNKNOWN, {"status": "warmup"}))
            continue
            
        label, flags, m, was_trending, was_high_vol = _infer_single_regime(
            trend_z[i], vol_ratio[i], drawdown[i], disp_ratio[i], 
            trend_dir[i], real_vol[i], avg_corr[i], corr_z[i],
            was_trending, was_high_vol, cfg 
        )
        
        states.append(RegimeState(label, flags, m))

    return states


def _infer_single_regime(
    dz: float, vr: float, dd: float, disp: float, td: float, rv: float, 
    avg_corr: float, corr_z: float, was_trending: bool, was_high_vol: bool,
    cfg: RegimeConfig
) -> tuple:
    """Helper to infer regime for a single bar (logic extraction for complexity)."""
    flags = set()
    label = RegimeLabel.RANGE_LOW_VOL
    
    # Panic Override
    if (dd < cfg.panic_drawdown and vr > cfg.panic_vol_spike) or (dd < cfg.panic_drawdown_extreme):
        label = RegimeLabel.PANIC
        flags.add(RegimeFlag.PANIC)
        is_trending = False
        is_high_vol = True 
    else:
        # Schmitt Trigger Logic
        th_trend = cfg.trend_th_exit if was_trending else cfg.trend_th_entry
        is_trending = dz > th_trend
        
        th_vol = cfg.vol_th_exit if was_high_vol else cfg.vol_th_entry
        is_high_vol = vr > th_vol
        
        if is_trending and is_high_vol:
            label = RegimeLabel.TREND_HIGH_VOL
        elif is_trending and not is_high_vol:
            label = RegimeLabel.TREND_LOW_VOL
        elif not is_trending and is_high_vol:
            label = RegimeLabel.RANGE_HIGH_VOL
        else:
            label = RegimeLabel.RANGE_LOW_VOL

    # Enrich Flags
    if disp > 1.5: 
         flags.add(RegimeFlag.DISPERSION_HIGH)
    if corr_z > cfg.corr_z_threshold:
         flags.add(RegimeFlag.CORR_SPIKE)

    m = {
        "trend_z": dz, "vol_ratio": vr, "drawdown": dd,
        "dispersion_ratio": disp, "trend_dir": td, "realized_vol_annual": rv,
        "avg_corr": avg_corr, "corr_z": corr_z,
    }
    return label, flags, m, is_trending, is_high_vol


def _infer_ml_regimes(
    metrics_df: pd.DataFrame, cfg: RegimeConfig
) -> List[RegimeState]:
    """
    Perform expanding/rolling K-Means clustering to classify market regimes.
    Auto-maps K centroids to RegimeLabels (TREND, HIGH_VOL, PANIC, RANGE).
    """
    import warnings
    # Local import to prevent slow initial module load for non-ML users
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        from sklearn.cluster import KMeans

    n = len(metrics_df)
    features = ["trend_z", "vol_ratio", "drawdown"]
    X = metrics_df[features].fillna(0).values

    labels_arr = np.zeros(n, dtype=int)
    cluster_to_label = {}
    current_model = None
    
    fit_window = getattr(cfg, "ml_fit_window", 252)
    clusters = getattr(cfg, "ml_clusters", 4)

    for i in range(n):
        if i < cfg.window:
            continue
            
        # Re-fit every 'fit_window' bars or on first valid bar
        if current_model is None or (i % fit_window == 0 and i >= cfg.window + clusters):
            start_ix = max(0, i - fit_window)
            X_train = X[start_ix:i]
            
            # Fallback if sparse
            if len(X_train) < clusters:
                X_train = X[0:i]
                
            if len(X_train) >= clusters:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    current_model = KMeans(n_clusters=clusters, random_state=42, n_init="auto")
                    current_model.fit(X_train)
                
                centroids = current_model.cluster_centers_
                # 0=trend_z, 1=vol_ratio, 2=drawdown
                panic_idx = int(np.argmin(centroids[:, 2]))  # Deepest drawdown
                remaining = [j for j in range(clusters) if j != panic_idx]
                
                cluster_to_label = {panic_idx: RegimeLabel.PANIC}
                
                if remaining:
                    med_trend = np.median(centroids[remaining, 0])
                    med_vol = np.median(centroids[remaining, 1])
                    for j in remaining:
                        c_trend, c_vol = centroids[j, 0], centroids[j, 1]
                        is_trend = c_trend >= med_trend
                        is_high_vol = c_vol >= med_vol
                        
                        if is_trend and is_high_vol:
                            cluster_to_label[j] = RegimeLabel.TREND_HIGH_VOL
                        elif is_trend and not is_high_vol:
                            cluster_to_label[j] = RegimeLabel.TREND_LOW_VOL
                        elif not is_trend and is_high_vol:
                            cluster_to_label[j] = RegimeLabel.RANGE_HIGH_VOL
                        else:
                            cluster_to_label[j] = RegimeLabel.RANGE_LOW_VOL

        if current_model is not None:
            pred = current_model.predict(X[i:i+1])[0]
            labels_arr[i] = pred
            
    states = []
    # Pre-fetch numpy arrays for mapping phase
    dd_arr = metrics_df["drawdown"].values
    vr_arr = metrics_df["vol_ratio"].values
    disp_arr = metrics_df["dispersion_ratio"].values
    corr_z_arr = metrics_df["corr_z"].values
    rv_arr = metrics_df["realized_vol_annual"].values
    dz_arr = metrics_df["trend_z"].values
    td_arr = metrics_df["trend_dir"].values
    ac_arr = metrics_df["avg_corr"].values
    
    for i in range(n):
        if i < cfg.window or current_model is None:
            states.append(RegimeState(RegimeLabel.UNKNOWN, {"status": "warmup"}))
            continue
            
        c_idx = labels_arr[i]
        label = cluster_to_label.get(c_idx, RegimeLabel.UNKNOWN)
        
        # Hard Panic Override (Same as Schmitt logic)
        flags = set()
        if (dd_arr[i] < cfg.panic_drawdown and vr_arr[i] > cfg.panic_vol_spike) or (dd_arr[i] < cfg.panic_drawdown_extreme):
            label = RegimeLabel.PANIC
            flags.add(RegimeFlag.PANIC)
            
        if disp_arr[i] > 1.5: 
            flags.add(RegimeFlag.DISPERSION_HIGH)
        if corr_z_arr[i] > cfg.corr_z_threshold:
            flags.add(RegimeFlag.CORR_SPIKE)
             
        m = {
            "trend_z": dz_arr[i], "vol_ratio": vr_arr[i], "drawdown": dd_arr[i],
            "dispersion_ratio": disp_arr[i], "trend_dir": td_arr[i], "realized_vol_annual": rv_arr[i],
            "avg_corr": ac_arr[i], "corr_z": corr_z_arr[i],
        }
        states.append(RegimeState(label, flags, m))
        
    return states


def detect_regime(  # noqa: PLR0912, PLR0915
    close_df: pd.DataFrame, asof: pd.Timestamp, cfg: RegimeConfig, previous_label: Optional[RegimeLabel] = None
) -> RegimeState:
    """
    Legacy Interface: Single-step detection.
    Note: calling this in a loop is purely inefficient now. Use preload/vectorized path.
    """
    # Slice up to asof
    subset = close_df.loc[:asof]
    if len(subset) < cfg.window + 1:
        return RegimeState(RegimeLabel.UNKNOWN, {"status": "insufficient_data"})
    
    metrics = compute_regime_indicators(subset, cfg)
    states = infer_regimes_from_metrics(metrics, cfg)
    return states[-1] if states else RegimeState(RegimeLabel.UNKNOWN)


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
