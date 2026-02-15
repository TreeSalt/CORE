"""
Vanguard Effective: Control Variable Benchmarking.

Generates deterministic benchmark metrics (equal-weight buy-and-hold)
for comparison against the active portfolio.
"""

from typing import Any, Dict

import numpy as np
import pandas as pd


def compute_equal_weight_benchmark(
    close_prices_df: pd.DataFrame,
    periods_per_year: int,
    initial_cash: float = 100_000.0,
) -> Dict[str, Any]:
    """
    Benchmark A: Equal-weight buy-and-hold of all symbols.
    Rebalanced once at start (no turnover).

    Returns dict with: total_return, sharpe, max_dd, equity_series.
    """
    if close_prices_df.empty:
        return _empty_benchmark()

    # Returns-based equity (scale-invariant)
    daily_returns = close_prices_df.pct_change().fillna(0)
    basket_returns = daily_returns.mean(axis=1)  # Equal weight

    equity = initial_cash * (1 + basket_returns).cumprod()
    total_return = float((equity.iloc[-1] / initial_cash) - 1.0)

    mean_r = basket_returns.mean()
    std_r = basket_returns.std()
    sharpe = float((mean_r / std_r) * np.sqrt(periods_per_year)) if std_r > 1e-9 else 0.0  # noqa: PLR2004

    peak = equity.cummax()
    dd = (equity / peak) - 1.0
    max_dd = float(dd.min())

    return {
        "benchmark_total_return_pct": round(total_return * 100, 2),
        "benchmark_sharpe_ratio": round(sharpe, 2),
        "benchmark_max_drawdown_pct": round(max_dd * 100, 2),
        "benchmark_equity_series": equity,
    }


def compute_alpha_metrics(
    portfolio_equity: pd.Series,
    benchmark_equity: pd.Series,
    periods_per_year: int,
) -> Dict[str, Any]:
    """
    Compute excess return, tracking error, information ratio,
    and max drawdown difference between portfolio and benchmark.
    """
    if portfolio_equity.empty or benchmark_equity.empty:
        return {
            "excess_return_pct": 0.0,
            "tracking_error": 0.0,
            "information_ratio": 0.0,
            "max_dd_diff_pct": 0.0,
        }

    # Align on common index
    common = portfolio_equity.index.intersection(benchmark_equity.index)
    if len(common) < 2:  # noqa: PLR2004
        return {
            "excess_return_pct": 0.0,
            "tracking_error": 0.0,
            "information_ratio": 0.0,
            "max_dd_diff_pct": 0.0,
        }

    port = portfolio_equity.reindex(common)
    bench = benchmark_equity.reindex(common)

    port_ret = port.pct_change().fillna(0)
    bench_ret = bench.pct_change().fillna(0)

    excess = port_ret - bench_ret
    excess_total = float((port.iloc[-1] / port.iloc[0]) - (bench.iloc[-1] / bench.iloc[0]))

    tracking_error = float(excess.std() * np.sqrt(periods_per_year)) if len(excess) > 1 else 0.0
    info_ratio = float(excess.mean() / excess.std() * np.sqrt(periods_per_year)) if excess.std() > 1e-9 else 0.0  # noqa: PLR2004

    # MaxDD diff
    port_dd = float(((port / port.cummax()) - 1.0).min())
    bench_dd = float(((bench / bench.cummax()) - 1.0).min())
    dd_diff = port_dd - bench_dd  # Negative = portfolio had worse DD

    return {
        "excess_return_pct": round(excess_total * 100, 2),
        "tracking_error": round(tracking_error, 4),
        "information_ratio": round(info_ratio, 2),
        "max_dd_diff_pct": round(dd_diff * 100, 2),
    }


def _empty_benchmark() -> Dict[str, Any]:
    return {
        "benchmark_total_return_pct": 0.0,
        "benchmark_sharpe_ratio": 0.0,
        "benchmark_max_drawdown_pct": 0.0,
        "benchmark_equity_series": pd.Series(dtype=float),
    }
