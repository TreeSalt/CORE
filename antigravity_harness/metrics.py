from __future__ import annotations

from typing import Any, Dict, List

import numpy as np
import pandas as pd


def max_drawdown(equity: pd.Series) -> float:
    if equity.empty:
        return 0.0
    peak = equity.cummax()
    # HYDRA GUARD: Zero-Div Chaos (Vector 102)
    if (peak == 0).any():
         return 0.0
    dd = (equity / peak) - 1.0
    return float(dd.min()) * -1.0  # positive fraction (e.g., 0.25 = -25%)


def cagr(equity: pd.Series, periods_per_year: int) -> float:
    if equity.empty:
        return 0.0
    start = float(equity.iloc[0])
    end = float(equity.iloc[-1])
    if start <= 0:
        return 0.0

    # Use n_bars / periods_per_year for dynamic annualization
    # 1.1 -> n_bars = 100, ppy=252 -> years = 100/252 = 0.39
    n_days = len(equity) - 1
    if n_days <= 0:
        return 0.0
    years = n_days / float(periods_per_year)
    # HYDRA GUARD: Zero-Div Chaos (Vector 102)
    if years == 0:
        return 0.0
    return float((end / start) ** (1 / years) - 1.0)


def daily_sharpe(equity: pd.Series, periods: int) -> float:
    if equity.empty:
        return 0.0
    daily = equity.resample("D").last().ffill()
    rets = daily.pct_change().dropna()
    if rets.empty:
        return 0.0
    mu = rets.mean() * float(periods)
    sigma = rets.std() * np.sqrt(float(periods))
    if sigma == 0 or np.isnan(sigma):
        return 0.0
    return float(mu / sigma)  # rf=0


def profit_factor(trades: List[Any]) -> float:
    if not trades:
        return float("nan")
    gains = sum(float(t.pnl_abs) for t in trades if float(t.pnl_abs) > 0)
    losses = -sum(float(t.pnl_abs) for t in trades if float(t.pnl_abs) < 0)
    # Strict-mode stabilization: PF must be finite.
    if losses <= 0.0:
        if gains <= 0.0:
            return 1.0
        pf = gains / 1e-12
        return float(min(pf, 1e6))
    return float(gains / losses)


def kelly_fraction(trades: List[Any]) -> float:
    """
    Calculates the Kelly Criterion fraction: K% = W - (1 - W) / R
    W = Win Rate, R = Win/Loss Ratio (Avg Win / Avg Loss)
    Returns the recommended risk fraction (e.g., 0.20 for 20% risk).
    """
    if not trades:
        return 0.0

    wins = [float(t.pnl_pct) for t in trades if float(t.pnl_abs) > 0]
    losses = [abs(float(t.pnl_pct)) for t in trades if float(t.pnl_abs) < 0]

    if not wins or not losses:
        return 0.0

    win_rate = len(wins) / len(trades)
    avg_win = np.mean(wins)
    avg_loss = np.mean(losses)

    if avg_loss == 0:
        return 1.0  # Perfect strategy (in theory)

    win_loss_ratio = avg_win / avg_loss
    k = win_rate - (1 - win_rate) / win_loss_ratio

    return float(max(0.0, k))


def expectancy(trades: List[Any]) -> float:
    """Average per-trade return (pct), not annualized."""
    if not trades:
        return float("nan")
    return float(np.mean([float(t.pnl_pct) for t in trades]))


def monte_carlo_shuffled_drawdown(trades: List[Any], iterations: int = 100, initial_equity: float = 10000.0) -> float:
    """
    Shuffles trade PnL (absolute) to simulate different possible equity curves.
    Returns the 95th percentile of Maximum Drawdown across all iterations.
    """
    if not trades or iterations <= 0:
        return 0.0

    pnls = [float(t.pnl_abs) for t in trades]
    max_dds = []

    for _ in range(iterations):
        # Shuffle trades
        shuffled = np.random.choice(pnls, size=len(pnls), replace=False)
        
        # Build equity curve
        curve = [initial_equity]
        for p in shuffled:
            curve.append(curve[-1] + p)
            
        # Calc MaxDD for this curve
        curve_s = pd.Series(curve)
        max_dds.append(max_drawdown(curve_s))

    return float(np.percentile(max_dds, 95))


def calculate_var(equity: pd.Series, confidence: float = 0.95) -> float:
    """
    Calculates historical Value at Risk (VaR) at the specified confidence level.
    VaR represents the minimum loss expected over a period at a given confidence level.
    """
    if equity.empty or len(equity) < 2:
        return 0.0
    
    # Calculate returns
    if isinstance(equity.index, pd.DatetimeIndex):
        daily = equity.resample("D").last().ffill()
        rets = daily.pct_change().dropna()
    else:
        # Fallback to period-to-period returns if no DatetimeIndex
        rets = equity.pct_change().dropna()
    
    if rets.empty:
        return 0.0
        
    # Historical VaR: Percentile of returns
    var_val = np.percentile(rets, (1 - confidence) * 100)
    return float(abs(min(0.0, var_val)))


def calmar_ratio(cagr_val: float, max_dd: float) -> float:
    if max_dd == 0.0:
        return 0.0 if cagr_val <= 0 else 100.0  # Cap at 100 for perfect run
    return cagr_val / abs(max_dd)


def compute_metrics(equity: pd.Series, trades: List[Any], periods_per_year: int, symbol: str = "SPY") -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    if equity.empty:
        initial = 0.0
        final = 0.0
    else:
        initial = float(equity.iloc[0])
        final = float(equity.iloc[-1])

    annualization = periods_per_year

    out["initial_equity"] = initial
    out["final_equity"] = final
    out["final_equity_ratio"] = (final / initial) if initial else 0.0
    out["total_return"] = (final / initial - 1.0) if initial else 0.0

    cagr_val = cagr(equity, periods_per_year=annualization)
    max_dd = max_drawdown(equity)

    out["cagr"] = cagr_val
    out["max_drawdown"] = max_dd
    out["trade_count"] = len(trades)
    out["entry_fills"] = len(trades)
    out["exit_fills"] = len(trades)

    # Open at end = trades forced closed
    out["open_positions_at_end"] = sum(1 for t in trades if getattr(t, "exit_reason", "") == "force_close")

    out["profit_factor"] = profit_factor(trades)
    out["expectancy"] = expectancy(trades)
    out["daily_sharpe"] = daily_sharpe(equity, periods=annualization)

    # Phase 6c: Profit Engine Metrics
    wins = sum(1 for t in trades if float(t.pnl_abs) > 0)
    out["win_rate"] = (wins / len(trades)) if trades else 0.0

    calmar = calmar_ratio(cagr_val, max_dd)
    out["calmar_ratio"] = calmar

    # ProfitScore: Business Scalability Metric
    # Rewards Risk-Adj Return (Calmar) AND Frequency (Log Trades)
    # A straetgy with Calmar 2.0 and 1 trade is luck (Score ~0.7)
    # A strategy with Calmar 2.0 and 100 trades is business (Score ~9.2)
    out["profit_score"] = calmar * np.log1p(len(trades))

    # Phase 6: Gate Compatibility Aliases
    out["max_dd_pct"] = out["max_drawdown"]
    out["sharpe_ratio"] = out["daily_sharpe"]
    out["expectancy_pct"] = out["expectancy"]

    out["kelly_fraction"] = kelly_fraction(trades)
    out["var_95"] = calculate_var(equity, confidence=0.95)
    
    # Item 9: Monte Carlo Robustness
    # iterations could be passed in, but we'll use a conservative default or look at trades count
    mc_iters = 100 if len(trades) < 50 else 250
    out["mc_drawdown_95"] = monte_carlo_shuffled_drawdown(trades, iterations=mc_iters, initial_equity=initial)

    return out


def buy_and_hold_cagr(df: pd.DataFrame, periods_per_year: int) -> float:
    if df.empty:
        return 0.0
    equity = (df["Close"] / float(df["Close"].iloc[0])).astype(float)
    return cagr(equity, periods_per_year=periods_per_year)
