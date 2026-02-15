from __future__ import annotations

import numpy as np
import pandas as pd


def SMA(series: pd.Series, period: int) -> pd.Series:
    return series.rolling(window=period, min_periods=period).mean()


sma = SMA


def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Wilder RSI (EMA with alpha=1/period)."""
    delta = series.diff()
    gain = delta.clip(lower=0.0)
    loss = (-delta).clip(lower=0.0)

    avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()

    # Physics Correction:
    # If avg_loss is 0, RSI is 100 (perfect overbought / trending up)
    # If avg_gain is 0, RSI is 0 (perfect oversold / trending down)

    # We use np.where to handle the vector safely
    rs = np.where(avg_loss > 0, avg_gain / avg_loss.replace(0.0, np.nan), np.nan)

    out = 100 - (100 / (1 + rs))

    # Final cleanup: map NaNs
    # If avg_loss was 0 and avg_gain > 0 -> rs=inf -> 100
    # If avg_gain was 0 and avg_loss > 0 -> rs=0 -> 0
    # If both are 0 (flat) -> 50
    out = np.where(avg_loss == 0, 100.0, out)
    out = np.where((avg_gain == 0) & (avg_loss > 0), 0.0, out)
    out = np.where((avg_gain == 0) & (avg_loss == 0), 50.0, out)

    return pd.Series(out, index=series.index).ffill().fillna(50.0)


def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Average True Range (Wilder). Requires columns: High, Low, Close."""
    high = df["High"]
    low = df["Low"]
    close = df["Close"]

    prev_close = close.shift(1)
    tr = pd.concat(
        [
            (high - low).abs(),
            (high - prev_close).abs(),
            (low - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)

    out = tr.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    return out
