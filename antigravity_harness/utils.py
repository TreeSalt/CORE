from __future__ import annotations

import os
import subprocess
from typing import Any

import pandas as pd

from antigravity_harness import __version__


def get_version_str() -> str:
    """
    Returns the version string, optionally appended with the short git hash.
    e.g. "4.3.1" or "4.3.1+g3a1b2c"
    """
    v = __version__
    try:
        # Get short git hash
        # 2>/dev/null to silence errors if not a git repo
        h = (
            subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], stderr=subprocess.DEVNULL)
            .decode("utf-8")
            .strip()
        )
        if h:
            v += f"+g{h}"
    except Exception:
        pass
    return v


def safe_to_csv(df: Any, path: str, **kwargs) -> None:
    """
    Writes DataFrame to CSV, ensuring headers are written even if DataFrame is empty.
    """
    # If it's a list (from JSON conversion), convert back to DataFrame or handle gracefully
    if isinstance(df, list):
        df = pd.DataFrame(df)

    if hasattr(df, "empty") and df.empty:
        pass

    # Ensure directory exists
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    if hasattr(df, "to_csv"):
        df.to_csv(path, **kwargs)


def safe_read_csv(path: str, **kwargs) -> pd.DataFrame:
    """
    Reads CSV gracefully. If file exists but is empty (only headers or 0 bytes),
    handles it.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")

    try:
        return pd.read_csv(path, **kwargs)
    except pd.errors.EmptyDataError:
        # Return empty DataFrame
        # We might not know columns if it's 0 bytes.
        # If it's 0 bytes, we can't infer columns.
        # But usually we want to return *something*.
        return pd.DataFrame()


def infer_periods_per_year(interval: str, is_crypto: bool = True) -> int:
    """
    Phase 10.3: Physics Hardening (Asset Class Aware).
    Infer annualization factor from interval string.

    Args:
        interval: e.g. "1d", "4h", "15m"
        is_crypto: If True, uses 365 days. If False (Equity/Fiat), uses 252 days.
    """
    interval = interval.lower().strip()
    base_days = 365 if is_crypto else 252
    minutes_per_day = 1440 if is_crypto else 390  # equities: 6.5h session

    if interval == "1d":
        return base_days

    # Unit parsing
    if interval.endswith("h"):
        try:
            val = int(interval[:-1])
            hours_per_day = minutes_per_day / 60.0
            return int(round(base_days * (hours_per_day / val)))
        except (ValueError, IndexError):
            pass

    if interval.endswith("m"):
        try:
            val = int(interval[:-1])
            return int(round(base_days * (minutes_per_day / val)))
        except (ValueError, IndexError):
            pass

    # Default fallback
    print(f"⚠️ Warning: Unknown interval '{interval}', defaulting to {base_days}")
    return base_days
