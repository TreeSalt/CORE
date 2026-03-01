# antigravity_harness/data_loader.py
import hashlib
from pathlib import Path
from typing import Tuple

import pandas as pd

try:
    import pyarrow.parquet as pq

    HAS_PYARROW = True
except ImportError:
    HAS_PYARROW = False


class ZeroCopyLoader:
    @staticmethod
    def load_market_data(path: Path) -> pd.DataFrame:
        if not path.exists():
            raise FileNotFoundError(f"Missing: {path}")
        if path.suffix != ".parquet":
            raise ValueError("THE DRAGON FORBIDS CSV.")

        # MISSION v4.5.382: Synthetic Data Prohibition (LAW 2.7)
        if "synthetic" in path.name.lower() or "synthetic" in str(path).lower():
            raise RuntimeError(
                f"SMOKE_BLOCKED_SYNTHETIC_DATA: Path contains 'synthetic': {path}. "
                "Core execution must use 'data_provenance: real'."
            )

        if not HAS_PYARROW:
            raise ImportError("pyarrow is required for Parquet support.")

        table = pq.read_table(path, memory_map=True)
        df = table.to_pandas(self_destruct=True, split_blocks=True)
        
        # MISSION v4.5.360: Ensure DatetimeIndex for chronological physics
        if "Datetime" in df.columns:
            df["Datetime"] = pd.to_datetime(df["Datetime"])
            df.set_index("Datetime", inplace=True)
        elif not isinstance(df.index, pd.DatetimeIndex):
            # Try to infer if possible, but usually we expect 'Datetime' col in our repo
            pass
            
        return df

    @staticmethod
    def convert_csv_to_parquet(csv_path: Path):
        # MISSION v4.5.360: Parse dates during ingestion
        df = pd.read_csv(csv_path, parse_dates=["Datetime"])
        parquet_path = csv_path.with_suffix(".parquet")
        # Keep index=True to preserve DatetimeIndex if it was set, 
        # but here we'll just ensure it's in the columns for load_market_data to handle.
        df.to_parquet(parquet_path, compression="snappy", index=False)
        print(f"⚡ [SPEED] Transmuted {csv_path.name} to Binary Artifact.")


    @staticmethod
    def hash_raw_data(df: pd.DataFrame) -> str:
        """MISSION v4.5.360: Deterministic hash of OHLCV values."""
        # Use only OHLCV columns for hashing to ensure feature invariance
        cols = ["Open", "High", "Low", "Close", "Volume"]
        cols_available = [c for c in cols if c in df.columns]
        
        # We use JSON serialization of values for cross-platform/version hash stability
        # Sorting by index to ensure chronological determinism
        data_str = df[cols_available].sort_index().to_json(orient="values")
        return hashlib.sha256(data_str.encode("utf-8")).hexdigest()

    @classmethod
    def split_is_oos(cls, df: pd.DataFrame, oos_split: float = 0.2) -> Tuple[pd.DataFrame, pd.DataFrame, str, str]:
        """
        MISSION v4.5.360: Chronological IS/OOS Split.
        Returns: (df_is, df_oos, is_hash, oos_hash)
        """
        if oos_split <= 0 or oos_split >= 1:
            return df, pd.DataFrame(), cls.hash_raw_data(df), "N/A"

        n = len(df)
        split_idx = int(n * (1 - oos_split))
        
        # Chronological split
        df_sorted = df.sort_index()
        df_is = df_sorted.iloc[:split_idx].copy()
        df_oos = df_sorted.iloc[split_idx:].copy()

        # LEAKAGE GATE (Strict verify)
        if not df_oos.empty:
            is_max = df_is.index.max()
            oos_min = df_oos.index.min()
            if is_max >= oos_min:
                raise RuntimeError(
                    f"DATA LEAKAGE DETECTED: IS End ({is_max}) is not strictly before OOS Start ({oos_min})."
                )

        is_hash = cls.hash_raw_data(df_is)
        oos_hash = cls.hash_raw_data(df_oos) if not df_oos.empty else "N/A"

        return df_is, df_oos, is_hash, oos_hash

    @staticmethod
    def load_orthogonal_csv(
        path: Path,
        timestamp_col: str = "timestamp",
        value_col: str = "sentiment_score",
        lag_seconds: int = 300,
    ) -> pd.Series:
        """
        MISSION v4.5.370: Load orthogonal (non-price) data from a local CSV.
        Enforces anti-lookahead lag rule: shifts observation timestamps forward
        by `lag_seconds` so that sentiment observed at time T is only available
        at time T + lag_seconds in the backtest.

        Returns a pd.Series indexed by lagged timestamp with values from value_col.
        Raises FileNotFoundError if the file is missing (caller must set BLOCKED_NO_ALT_DATA).
        """
        if not path.exists():
            raise FileNotFoundError(
                f"BLOCKED_NO_ALT_DATA: Orthogonal data file missing: {path}. "
                "STOP CONDITION: Do NOT generate synthetic alternative data."
            )

        df = pd.read_csv(path)

        if timestamp_col not in df.columns or value_col not in df.columns:
            raise ValueError(
                f"Orthogonal CSV must contain columns [{timestamp_col}, {value_col}]. "
                f"Found: {list(df.columns)}"
            )

        if df.empty:
            raise FileNotFoundError(
                f"BLOCKED_NO_ALT_DATA: Orthogonal data file is empty: {path}."
            )

        # Parse timestamps and enforce lag rule
        df[timestamp_col] = pd.to_datetime(df[timestamp_col], utc=True)
        df = df.sort_values(timestamp_col)

        # ANTI-LOOKAHEAD LAG: shift timestamps forward by lag_seconds
        # This means a sentiment observation at 09:30 with lag=300s
        # is only "available" to the backtest at 09:35.
        lag_delta = pd.Timedelta(seconds=lag_seconds)
        df["lagged_ts"] = df[timestamp_col] + lag_delta

        series = pd.Series(
            data=df[value_col].values,
            index=pd.DatetimeIndex(df["lagged_ts"]),
            name=value_col,
        )
        series.index.name = "Datetime"

        # Provenance hash for audit trail
        _raw_json = series.to_json(None, orient="values")  # type: ignore[call-overload]
        data_str: str = _raw_json if _raw_json is not None else "[]"
        provenance_hash = hashlib.sha256(data_str.encode("utf-8")).hexdigest()
        print(
            f"📡 Orthogonal Data Loaded: {path.name} | "
            f"{len(series)} observations | Lag: {lag_seconds}s | "
            f"Provenance: {provenance_hash[:12]}"
        )

        return series

