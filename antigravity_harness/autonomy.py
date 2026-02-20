import hashlib
import os
from datetime import timedelta
from typing import Any, Dict, Tuple

import pandas as pd

from antigravity_harness.config import DataConfig, EngineConfig, GateThresholds, StrategyParams
from antigravity_harness.context import SimulationContextBuilder
from antigravity_harness.data import load_ohlc
from antigravity_harness.essence import EssenceLab
from antigravity_harness.paths import INTEL_DIR, SNAPSHOT_DIR
from antigravity_harness.runner import SovereignRunner
from antigravity_harness.strategies import STRATEGY_REGISTRY
from antigravity_harness.strategies.registry import StrategyRegistry
from antigravity_harness.utils import safe_to_csv


def _compute_file_hash(path: str) -> str:
    """Compute SHA256 of the physical file content bytes."""
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def get_snapshot_path(symbol: str, timeframe: str, end_date: str, content_hash: str) -> str:
    h8 = content_hash[:8]
    safe_end = end_date.replace("-", "").replace(":", "")[:8]
    fname = f"{symbol}_{timeframe}_{safe_end}_{h8}.csv"
    return os.path.join(SNAPSHOT_DIR, fname)


def save_snapshot(symbol: str, start: str, end: str, timeframe: str) -> Tuple[str, str]:
    """Fetch data, save to CSV, compute hash of file, rename with hash. Returns (path, hash)."""
    os.makedirs(SNAPSHOT_DIR, exist_ok=True)

    cfg = DataConfig(interval=timeframe)
    try:
        df = load_ohlc(symbol, start, end, cfg)
    except Exception:
        df = pd.DataFrame()

    if df.empty:
        raise ValueError(f"Snapshot Failed: No data for {symbol}")

    temp_name = f"temp_{symbol}_{timeframe}_{end}.csv"
    temp_path = os.path.join(SNAPSHOT_DIR, temp_name)

    safe_to_csv(df, temp_path)

    full_hash = _compute_file_hash(temp_path)
    final_path = get_snapshot_path(symbol, timeframe, end, full_hash)

    if os.path.exists(final_path):
        os.remove(temp_path)
        return final_path, full_hash

    os.rename(temp_path, final_path)
    return final_path, full_hash


def load_snapshot(path: str) -> pd.DataFrame:
    """Load snapshot and verify hash immediately."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Snapshot missing: {path}")

    fname = os.path.basename(path)
    try:
        parts = fname.replace(".csv", "").split("_")
        expected_h8 = parts[-1]
    except Exception:
        expected_h8 = "unknown"

    actual_hash = _compute_file_hash(path)
    actual_h8 = actual_hash[:8]

    if expected_h8 not in ("unknown", actual_h8):
        raise ValueError(f"DATA INTEGRITY ERROR: Hash mismatch for {path}. Expected {expected_h8}, got {actual_h8}.")

    df = pd.read_csv(path, index_col=0, parse_dates=True)
    for c in ["Open", "High", "Low", "Close", "Volume"]:
        if c in df.columns:
            df[c] = df[c].astype(float)

    return df


def walk_forward_validation(  # noqa: PLR0913
    symbol: str,
    timeframe: str,
    snapshot_path: str,
    profile_name: str,
    strategy_name: str,
    params: StrategyParams,
    train_days: int = 365,
    test_days: int = 90,
    step_days: int = 30,
    registry: StrategyRegistry = STRATEGY_REGISTRY,
    engine_cfg: Optional[EngineConfig] = None,
) -> Dict[str, Any]:

    # 1. Setup Configuration
    if engine_cfg is None:
        engine_cfg = EngineConfig()

    # 2. Load Immutable Data

    # 2. Check Coverage
    total_days = (df.index[-1] - df.index[0]).days
    if total_days < (train_days + test_days):
        return {"status": "FAIL", "reason": "Insufficient History"}

    splits = []
    start_dt = df.index[0]
    end_dt = df.index[-1]

    # 3. Rolling Loop
    curr = start_dt + timedelta(days=train_days)

    while (curr + timedelta(days=test_days)) <= end_dt:
        train_start = curr - timedelta(days=train_days)
        test_start = curr + timedelta(seconds=1)
        test_end = curr + timedelta(days=test_days)

        ts_str = test_start.isoformat()
        te_str = test_end.isoformat()

        # 4. Strict Slicing (No Leakage)
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)

        # We pass the slice [train_start, test_end] to backtest
        # Engine will use params.ma_length warmup implicitly.
        df_slice = df[(df.index >= train_start) & (df.index <= test_end)].copy()

        try:
            strat = registry.instantiate(strategy_name)
            runner = SovereignRunner(registry=registry)

            ctx = (
                SimulationContextBuilder()
                .with_strategy(strategy_name, strat)
                .with_params(params)
                .with_data_cfg(DataConfig(interval=timeframe))
                .with_engine_cfg(engine_cfg)
                .with_thresholds(GateThresholds())
                .with_symbol(symbol)
                .with_window(ts_str, te_str)
                .with_gate_profile(profile_name)
                .with_override_df(df_slice)
                .with_intelligence(EssenceLab(INTEL_DIR).get_consensus_signal(["MARKET_PULSE", "MARKET_ALPHA"]))
                .build()
            )

            res = runner.run_simulation(ctx)

            p = res.profit_status
            s = res.safety_status
            pf = res.metrics.profit_factor

            splits.append({"test_start": ts_str, "test_end": te_str, "profit_status": p, "safety_status": s, "pf": pf})

        except Exception as e:
            splits.append(
                {
                    "test_start": ts_str,
                    "test_end": te_str,
                    "profit_status": "FAIL",
                    "safety_status": "FAIL",
                    "pf": 0.0,
                    "error": str(e),
                }
            )

        curr += timedelta(days=step_days)

    if not splits:
        return {"status": "FAIL", "reason": "No Splits"}

    pass_count = sum(1 for r in splits if r["profit_status"] == "PASS")
    safety_fails = sum(1 for r in splits if r["safety_status"] == "FAIL")
    safety_warns = sum(1 for r in splits if r["safety_status"] == "WARN")

    pass_ratio = pass_count / len(splits) if len(splits) > 0 else 0.0

    wf_status = "PASS"
    reason = f"Passed {pass_count}/{len(splits)} splits ({pass_ratio:.1%})"

    if safety_fails > 0:
        wf_status = "FAIL"
        reason = f"Safety Fail in {safety_fails} splits"
    elif pass_ratio < 0.60:  # noqa: PLR2004
        wf_status = "FAIL"
        reason = f"Profit Consistency {pass_ratio:.1%} < 60%"
    elif safety_warns > 0:
        wf_status = "WARN"
        reason += f" (Safety Warns: {safety_warns})"

    return {"status": wf_status, "reason": reason, "splits": splits, "pass_ratio": pass_ratio}
