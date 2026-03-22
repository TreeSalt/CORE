from __future__ import annotations

import contextlib
import hashlib
import os
from typing import Any, cast

import pandas as pd

try:
    import yfinance as yf
except ImportError:
    yf = None

from mantis_core.config import DataConfig


def _cache_key(symbol: str, start: str, end: str, cfg: DataConfig) -> str:
    raw = f"{symbol}|{start}|{end}|{cfg.interval}|{cfg.auto_adjust}|{cfg.adjust_dividends}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def resample_ohlc(df: pd.DataFrame, timeframe: str) -> pd.DataFrame:
    """Resample OHLCV data into a higher timeframe (e.g., '4H', '12H', '1D')."""
    if df.empty:
        return df

    # Mapping for OHLCV resampling
    logic = {"Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"}

    # Filter only available columns
    available_logic = {k: v for k, v in logic.items() if k in df.columns}

    # Resample
    resampled = df.resample(timeframe).agg(cast(Any, available_logic))
    return resampled.dropna()


def _cache_path(cache_dir: str, key: str) -> str:
    os.makedirs(cache_dir, exist_ok=True)
    return os.path.join(cache_dir, f"{key}.pkl")


def _get_splits(ticker: Any) -> pd.Series:
    # yfinance exposes splits as a Series indexed by date
    try:
        s = ticker.splits
    except Exception:
        s = pd.Series(dtype=float)
    if s is None:
        return pd.Series(dtype=float)
    s = s.dropna()
    # Ensure timezone-naive index for consistent joins
    if hasattr(s.index, "tz") and s.index.tz is not None:
        s.index = s.index.tz_convert(None)
    return s


def _apply_splits_backward(df: pd.DataFrame, splits: pd.Series) -> pd.DataFrame:
    """Apply split factors to historical prices (backward adjustment).

    For a split factor k on date D (e.g., 2.0 for 2-for-1), all prices
    *before* D are divided by k; volumes are multiplied by k.
    """
    if splits.empty:
        return df

    out = df.copy()
    splits = splits.sort_index()

    # cumulative factor applied to rows before each split date
    factor = pd.Series(1.0, index=out.index)

    for date, k in splits.items():
        if k is None or k == 0:
            continue
        mask = factor.index < pd.Timestamp(str(date))
        factor.loc[mask] /= float(k)

    for col in ["Open", "High", "Low", "Close"]:
        out[col] = out[col] * factor

    if "Adj Close" in out.columns:
        out["Adj Close"] = out["Adj Close"] * factor

    if "Volume" in out.columns:
        out["Volume"] = (out["Volume"] / factor).round()

    return out


def load_ohlc(symbol: str, start: str, end: str, cfg: DataConfig, use_network: bool = True) -> pd.DataFrame:  # noqa: PLR0912, PLR0915
    """Load OHLCV data with caching.

    Policy (per Fortress prompt):
      - Fetch raw OHLC (auto_adjust=False)
      - Apply split adjustments manually
      - Do not adjust dividends by default
    """
    key = _cache_key(symbol, start, end, cfg)
    path = _cache_path(cfg.cache_dir, key)

    if os.path.exists(path):
        # HYDRA GUARD: Symlink Mirror Protection (Vector 138)
        if os.path.islink(path):
            raise RuntimeError(f"SECURITY VIOLATION: Symlink detected at cache path '{path}'. Aborting.")
        return pd.read_pickle(path)

    if not use_network:
        # HYDRA GUARD: CSV Injection Protection (Vector 137)
        # If we were to load from a raw CSV file, we'd scan for malicious leading chars
        # Placeholder for future CSV integration
        raise RuntimeError(f"OFFLINE MODE: Data for {symbol} not found in {path} and network fetch disabled.")

    if yf is None:
        raise RuntimeError("yfinance is required for data fetching. Install with: pip install yfinance")

    t = yf.Ticker(symbol)

    # Phase 5 Resonance: Support NxH Resampling
    target_interval = cfg.interval.lower()
    fetch_interval = target_interval
    resample_needed = False

    # If interval is 4h, 6h, 8h, 12h, we fetch 1h and resample
    if target_interval in ["4h", "6h", "8h", "12h"]:
        fetch_interval = "1h"
        resample_needed = True

    try:
        df = t.history(start=start, end=end, interval=fetch_interval, auto_adjust=cfg.auto_adjust)
    except Exception as e:
        print(f"  [!] yfinance error: {e}")
        df = pd.DataFrame()

    if df.empty and not cfg.auto_adjust:
        print(f"  [!] Retrying {symbol} with auto_adjust=True...")
        with contextlib.suppress(Exception):
            df = t.history(start=start, end=end, interval=fetch_interval, auto_adjust=True)

    if df.empty:
        raise ValueError(
            f"No data returned for {symbol} ({start}..{end}) at {fetch_interval}. Check symbol or date range."
        )

    # normalize columns & index
    df = df.copy()
    df.index = pd.to_datetime(df.index)
    if hasattr(df.index, "tz") and df.index.tz is not None:
        df.index = df.index.tz_convert(None)

    # yfinance may return lowercase columns in some cases
    df.columns = [c.title() if c.lower() != "adj close" else "Adj Close" for c in df.columns]

    # Split adjust only (no dividends) per prompt.
    splits = _get_splits(t)
    df = _apply_splits_backward(df, splits)

    # Keep only what engine needs
    needed = [c for c in ["Open", "High", "Low", "Close", "Volume"] if c in df.columns]
    df = df[needed].dropna()

    # Coverage Guard (Phase 6d)
    req_start_dt = pd.to_datetime(start).tz_localize(None)
    req_end_dt = pd.to_datetime(end).tz_localize(None)

    # We only check coverage if we expected data.
    if not df.empty:
        # Check actual coverage
        act_start = df.index[0]
        act_end = df.index[-1]

        req_duration = (req_end_dt - req_start_dt).total_seconds()
        act_duration = (act_end - act_start).total_seconds()

        # Avoid division by zero
        if req_duration > 0:
            coverage_pct = act_duration / req_duration
            if coverage_pct < 0.90:  # noqa: PLR2004
                print(
                    f"  [!] Data Coverage Warning: Requested {start}..{end}, got {act_start.date()}..{act_end.date()} ({coverage_pct:.1%})"  # noqa: E501
                )
                # For Phase 6d strictness:
                raise ValueError(
                    f"CRITICAL: Data coverage {coverage_pct:.1%} < 90% for {symbol}. Truncated data detected."
                )

    # Resample if needed
    if resample_needed:
        if df.empty:
            raise ValueError(f"Data empty after filtering for {symbol}")

        raw_count = len(df)
        df = resample_ohlc(df, target_interval)
        res_count = len(df)

        print(f"  [i] Resampled {symbol} {fetch_interval}->{target_interval}: {raw_count} -> {res_count} bars")

        if df.empty:
            raise ValueError(f"Data empty after resampling to {target_interval} for {symbol}")

    df.to_pickle(path)
    return df
