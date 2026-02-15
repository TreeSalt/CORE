from typing import Dict

import pandas as pd

from .indicators import SMA


def calculate_benchmarks(df: pd.DataFrame, initial_capital: float) -> Dict[str, pd.Series]:
    """
    Returns equity curves for:
    1. Buy & Hold
    2. SMA200 Trend Following (Always-in when above SMA200)
    """
    curves = {}

    # 1. Buy & Hold
    # Start at initial_capital, track pct change of Close
    returns = df["Close"].pct_change().fillna(0)
    curves["buy_and_hold"] = initial_capital * (1 + returns).cumprod()

    # 2. SMA200 Baseline
    # Compute SMA200
    sma200 = SMA(df["Close"], 200)
    # Signal: If today's Close > SMA200, we are invested for tomorrow.
    # We shift signal by 1 to apply today's decision to tomorrow's return.
    signal = (df["Close"] > sma200).shift(1).fillna(False)

    sma_returns = returns.copy()
    # Mask returns where signal is False (stay in cash, 0% return)
    sma_returns = sma_returns.where(signal, 0.0)
    curves["sma200_baseline"] = initial_capital * (1 + sma_returns).cumprod()

    return curves
