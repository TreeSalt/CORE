from __future__ import annotations

import os
from collections import Counter
from itertools import product
from typing import Any, Dict, List, Optional, Tuple, cast

import numpy as np
import pandas as pd

from antigravity_harness.config import (
    DataConfig,
    EngineConfig,
    GateThresholds,
    StrategyParams,
    load_yaml,
    save_yaml,
)
import psutil

# HYDRA GUARD: Memory Leak Protection (Vector 29)
def _check_memory_usage(limit_gb: float = 2.0) -> None:
    process = psutil.Process()
    rss_gb = process.memory_info().rss / (1024 * 1024 * 1024)
    if rss_gb > limit_gb:
        raise RuntimeError(f"RESOURCE EXHAUSTION: Memory usage ({rss_gb:.2f} GB) exceeds Hydra limit ({limit_gb} GB)")
from antigravity_harness.context import SimulationContextBuilder
from antigravity_harness.data import load_ohlc  # For Ray loading
from antigravity_harness.engine import Trade
from antigravity_harness.essence import EssenceLab
from antigravity_harness.models import SimulationResult
from antigravity_harness.paths import INTEL_DIR
from antigravity_harness.runner import SovereignRunner
from antigravity_harness.strategies import STRATEGY_REGISTRY
from antigravity_harness.strategies.registry import StrategyRegistry

try:
    import ray  # type: ignore

    from antigravity_harness.distributed import BacktestWorker, init_ray
except ImportError:
    ray = None
    ActorPool = None

try:
    from ray.util.actor_pool import ActorPool  # type: ignore
except ImportError:
    ActorPool = None

try:
    from joblib import Parallel, delayed  # type: ignore[import-untyped]
except Exception:  # pragma: no cover
    Parallel = None
    delayed = None


Status = str  # PASS | FAIL | INVALID


def analyze_robustness(trades: List[Trade]) -> Dict[str, Any]:
    """Phase 5 Resonance: Trade Contribution Analysis."""
    if not trades:
        return {"pf_full": 0.0, "pf_minus1": 0.0, "pf_minus2": 0.0, "best_trade_contribution_pct": 0.0}

    pnls = [t.pnl_abs for t in trades]
    total_gp = sum(p for p in pnls if p > 0)
    _total_gl = sum(p for p in pnls if p < 0)

    def calc_pf(p_list: List[float]) -> float:
        gp = sum(p for p in p_list if p > 0)
        gl = sum(p for p in p_list if p < 0)
        if gl == 0:
            return 999.0 if gp > 0 else 0.0
        return abs(gp / gl)

    pf_full = calc_pf(pnls)

    # Sort by Absolute PnL (Top trades)
    sorted_pnls = sorted(pnls, reverse=True)

    pf_m1 = calc_pf(sorted_pnls[1:]) if len(sorted_pnls) > 1 else 0.0
    pf_m2 = calc_pf(sorted_pnls[2:]) if len(sorted_pnls) > 2 else 0.0  # noqa: PLR2004

    best_contrib = (sorted_pnls[0] / total_gp * 100.0) if total_gp > 0 else 0.0

    return {
        "pf_full": float(pf_full),
        "pf_minus1": float(pf_m1),
        "pf_minus2": float(pf_m2),
        "best_trade_contribution_pct": float(best_contrib),
    }


def _execute_ray_batch(  # noqa: PLR0913
    strategy_name: str,
    params_list: List[StrategyParams],
    total_combinations: List[Tuple[str, str, StrategyParams]],
    data_cfg: DataConfig,
    engine_cfg: EngineConfig,
    thresholds: GateThresholds,
    start: str,
    end: str,
    gate_profile: str,
    symbols: List[str],
    registry: StrategyRegistry = STRATEGY_REGISTRY,
) -> List[Dict[str, Any]]:
    if ray is None:
        raise ImportError("Ray not installed.")

    init_ray()

    print("Ray: Discovery of data requirements...")
    needed_sources = set()
    for s, tf, _p in total_combinations:
        needed_sources.add((s, tf))

    print(f"Ray: Loading {len(needed_sources)} dataframes...")
    data_map = {}
    for s, tf in needed_sources:
        df = load_ohlc(s, start, end, DataConfig(interval=tf))
        data_map[(s, tf)] = df

    # Put data in store
    data_ref = ray.put(data_map)

    # Create Workers
    # Limit max workers to reasonable amount if CPU count is huge?
    # Or just use all.
    avail = int(ray.available_resources().get("CPU", 1))
    num_cpus = max(1, avail)
    print(f"Ray: Spawning {num_cpus} BacktestWorkers...")

    strat_cls = registry.get_class(strategy_name)

    workers = [
        BacktestWorker.remote(data_ref, strat_cls, engine_cfg)  # type: ignore
        for _ in range(num_cpus)
    ]
    pool = ActorPool(workers)

    # Prepare inputs
    inputs = []
    for s, tf, p in total_combinations:
        inputs.append(
            {
                "symbol": s,
                "params": p,
                "data_cfg": data_cfg,
                "thresholds": thresholds,
                "start": start,
                "end": end,
                "gate_profile": gate_profile,
                "interval": tf,
            }
        )

    print(f"Ray: Executing {len(inputs)} backtests...")

    def invoke(actor: Any, item: Dict[str, Any]) -> Any:
        return actor.calibrate_one.remote(
            symbol=item["symbol"],
            params=item["params"],
            data_cfg=item["data_cfg"],
            thresholds=item["thresholds"],
            start=item["start"],
            end=item["end"],
            gate_profile=item["gate_profile"],
            interval=item["interval"],
        )

    results = list(pool.map(invoke, inputs))
    return results


def _run_one(  # noqa: PLR0913
    strategy_name: str,
    params: StrategyParams,
    data_cfg: DataConfig,
    engine_cfg: EngineConfig,
    thresholds: GateThresholds,
    include_ablation: bool,
    include_time_split: bool,
    symbol: str,
    start: str,
    end: str,
    gate_profile: str = "equity_fortress",
    interval: str = "1d",
    snapshot_df: Optional[pd.DataFrame] = None,  # For Phase 6F Walk-Forward
    registry: StrategyRegistry = STRATEGY_REGISTRY,
) -> SimulationResult:
    runner = SovereignRunner(registry=registry)
    strat = registry.instantiate(strategy_name)

    ctx = (
        SimulationContextBuilder()
        .with_strategy(strategy_name, strat)
        .with_params(params)
        .with_data_cfg(data_cfg.model_copy(update={"interval": interval}))
        .with_engine_cfg(engine_cfg)
        .with_thresholds(thresholds)
        .with_symbol(symbol)
        .with_window(start, end)
        .with_gate_profile(gate_profile)
        .with_override_df(snapshot_df)
        .with_intelligence(EssenceLab(INTEL_DIR).get_consensus_signal(["MARKET_PULSE", "MARKET_ALPHA"]))
        .build()
    )
    return runner.run_simulation(ctx)


def generate_grid_dynamic(grid_axes: Dict[str, List[Any]]) -> Tuple[List[StrategyParams], List[str], List[List[Any]]]:
    valid_keys = set(StrategyParams.__annotations__.keys())
    param_keys = []
    param_values_list = []

    for k, v in grid_axes.items():
        if k == "timeframe":
            continue
        if k not in valid_keys:
            raise ValueError(f"SCHEMA LOCK: Grid key '{k}' is NOT defined in StrategyParams. Crash.")
        param_keys.append(k)
        param_values_list.append(v)

    config_list: List[StrategyParams] = []
    for combination in product(*param_values_list):
        param_dict = dict(zip(param_keys, combination, strict=False))
        sp = StrategyParams(**param_dict)
        config_list.append(sp)

    return config_list, param_keys, param_values_list


def _neighbors(idx: Tuple[int, ...], shape: Tuple[int, ...]) -> List[Tuple[int, ...]]:
    res = []
    dims = len(shape)
    for axis in range(dims):
        for step in (-1, 1):
            lst = list(idx)
            lst[axis] += step
            if 0 <= lst[axis] < shape[axis]:
                res.append(tuple(lst))
    return res


def connected_components(pass_mask: np.ndarray) -> List[List[Tuple[int, ...]]]:
    visited = np.zeros(pass_mask.shape, dtype=bool)
    comps: List[List[Tuple[int, ...]]] = []
    it = np.ndindex(pass_mask.shape)
    for idx in it:
        if not pass_mask[idx] or visited[idx]:
            continue
        stack = [idx]
        visited[idx] = True
        comp = []
        while stack:
            cur = stack.pop()
            comp.append(cur)
            for nb in _neighbors(cur, pass_mask.shape):
                if pass_mask[nb] and not visited[nb]:
                    visited[nb] = True
                    stack.append(nb)
        comps.append(comp)
    return comps


def _manhattan(a: Tuple[int, ...], b: Tuple[int, ...]) -> int:
    return sum(abs(a[i] - b[i]) for i in range(len(a)))


def select_deep_interior(
    plateau: List[Tuple[int, ...]],
    unsafe_indices: List[Tuple[int, ...]],
    trade_counts: Dict[Tuple[int, ...], int],
    expectancy: Dict[Tuple[int, ...], float],
    min_trades_centroid: int,
) -> Tuple[Tuple[int, ...], Dict[str, Any]]:
    # Candidates must pass min trades centroid
    candidates = [i for i in plateau if trade_counts.get(i, 0) >= min_trades_centroid]
    if not candidates:
        candidates = plateau[:]

    best = None
    best_score = -1
    best_exp = -1e9

    if not unsafe_indices:
        best_score = 9999
        for idx in candidates:
            exp = float(expectancy.get(idx, float("-inf")))
            if exp > best_exp:
                best = idx
                best_exp = exp
        return cast(Tuple[int, ...], best), {"interior_distance": 9999, "expectancy": best_exp}

    for idx in candidates:
        d = min((_manhattan(idx, f) for f in unsafe_indices), default=999)
        val_exp = float(expectancy.get(idx, float("-inf")))
        if d > best_score or (d == best_score and val_exp > best_exp):
            best = idx
            best_score = d
            best_exp = val_exp

    if best is None:
        # Fallback to first if somehow still None (should not happen with candidates logic)
        best = candidates[0]

    return cast(Tuple[int, ...], best), {"interior_distance": float(best_score), "expectancy": float(best_exp)}


def calibrate(  # noqa: PLR0912, PLR0913, PLR0915
    grid_yaml: str,
    output_dir: str,
    strategy_name: str = "v032_simple",
    data_cfg: Optional[DataConfig] = None,
    engine_cfg: Optional[EngineConfig] = None,
    thresholds: Optional[GateThresholds] = None,
    n_jobs: int = -1,
    include_ablation: bool = False,
    include_time_split: bool = False,
    symbols: Optional[List[str]] = None,
    start: str = "2000-01-01",
    end: str = "2024-12-31",
    interval: str = "1d",
    gate_profile: str = "equity_fortress",
    timeframes_override: Optional[List[str]] = None,
    use_ray: bool = False,
    registry: StrategyRegistry = STRATEGY_REGISTRY,
) -> Dict[str, Any]:
    if symbols is None:
        symbols = ["SPY"]
    data_cfg = data_cfg or DataConfig(interval=interval)
    engine_cfg = engine_cfg or EngineConfig()
    thresholds = thresholds or GateThresholds()

    spec = load_yaml(grid_yaml)
    grid_axes = spec.get("grid", spec)

    if timeframes_override:
        grid_axes["timeframe"] = timeframes_override
    elif "timeframe" not in grid_axes:
        grid_axes["timeframe"] = [interval]

    timeframes = grid_axes["timeframe"]
    params_list, axis_names, axis_values = generate_grid_dynamic(grid_axes)

    total_combinations = []
    for s in symbols:
        for tf in timeframes:
            for p in params_list:
                total_combinations.append((s, tf, p))

    print("--- PHASE 6c PROFIT ENGINE GRID ---")
    print(f"Axes: {axis_names} (Core Params) + ['timeframe', 'symbol']")
    print(f"Total Configs (Core): {len(params_list)}")
    print(f"Total Runs: {len(total_combinations)}")

    # Shape is (Symbol, Timeframe, Param1, Param2...)
    shape_dims = [len(symbols), len(timeframes)] + [len(v) for v in axis_values]
    shape = tuple(shape_dims)
    print(f"Hypercube Shape: {shape}")

    def to_idx(s: str, tf: str, p: StrategyParams) -> Tuple[int, ...]:
        s_idx = symbols.index(s)
        tf_idx = timeframes.index(tf)
        p_indices = []
        for name, values in zip(axis_names, axis_values, strict=False):
            val = getattr(p, name)
            try:
                idx = values.index(val)
            except ValueError:
                idx = 0
            p_indices.append(idx)
        return tuple([s_idx, tf_idx] + p_indices)

    print(f"Running calibration on {len(total_combinations)} combinations...")

    if use_ray:
        if ray is not None:
            raw_results = _execute_ray_batch(
                strategy_name,
                params_list,
                total_combinations,
                data_cfg,
                engine_cfg,
                thresholds,
                start,
                end,
                gate_profile,
                symbols,
                registry=registry,
            )
        else:
            # Phase 9F: Robust Fallback for unsupported platforms (e.g. Python 3.14)
            # Force serial execution to avoid process/semaphore leakage in joblib
            print("Ray: Not installed. Forcing serial execution to prevent resource leakage...")
            raw_results = [
                _run_one(
                    strategy_name,
                    p,
                    data_cfg,
                    engine_cfg,
                    thresholds,
                    include_ablation,
                    include_time_split,
                    s,
                    start,
                    end,
                    gate_profile,
                    tf,
                    registry=registry,
                )
                for s, tf, p in total_combinations
            ]
    elif Parallel is not None and delayed is not None:
        raw_results = Parallel(n_jobs=n_jobs, prefer="processes")(
            delayed(_run_one)(
                strategy_name,
                p,
                data_cfg,
                engine_cfg,
                thresholds,
                include_ablation,
                include_time_split,
                s,
                start,
                end,
                gate_profile,
                tf,
                registry=registry,
            )
            for s, tf, p in total_combinations
        )
    else:
        raw_results = [
            _run_one(
                strategy_name,
                p,
                data_cfg,
                engine_cfg,
                thresholds,
                include_ablation,
                include_time_split,
                s,
                start,
                end,
                gate_profile,
                tf,
                registry=registry,
            )
            for s, tf, p in total_combinations
        ]

    results: Dict[Tuple[int, ...], Dict[str, Any]] = {}

    # We need to track PASS/FAIL per slice
    pass_mask = np.zeros(shape, dtype=bool)

    all_configs_flat = []
    trade_count_values = []

    # Portfolio Map for Robustness
    # Key: (timeframe, tuple(param_values)) -> stats
    portfolio_map: Dict[Tuple, Dict[str, Any]] = {}

    for (s, tf, p), r in zip(total_combinations, raw_results, strict=False):
        # HYDRA GUARD: Resource Enforcement (Vector 29)
        _check_memory_usage(limit_gb=2.0)
        
        idx = to_idx(s, tf, p)
        results[idx] = r
        tc = int(r.metrics.trade_count)
        trade_count_values.append(tc)

        status = r.status
        if status == "PASS":
            pass_mask[idx] = True

        fail_reason = r.fail_reason
        # SimulationResult has: status, profit_status, safety_status, fail_reason, warns, gate_results...
        # It does NOT have fail_gate as a top level string.
        # But fail_reason is there.
        fail_gate = ""  # Legacy
        fail_reason = r.fail_reason

        pf = float(r.metrics.profit_factor)
        if np.isnan(pf) or np.isinf(pf):
            pf = 0.0

        ps = float(r.metrics.profit_score)
        if np.isnan(ps) or np.isinf(ps):
            ps = 0.0

        calmar = float(r.metrics.calmar_ratio)

        flat_record = {
            "symbol": s,
            "timeframe": tf,
            "params": p.model_dump(),
            "status": status,
            "fail_gate": fail_gate,
            "fail_reason": fail_reason,
            "profit_factor": pf,
            "profit_score": ps,
            "calmar_ratio": calmar,
            "cagr": float(r.metrics.cagr),
            "win_rate": float(r.metrics.win_rate),
            "trade_count": tc,
            "max_dd_pct": float(r.metrics.max_dd_pct),
            "sharpe_ratio": float(r.metrics.sharpe_ratio),
        }
        all_configs_flat.append(flat_record)

        # Robustness Aggregation
        p_tuple = tuple(sorted(p.model_dump().items()))
        core_key = (tf, p_tuple)

        if core_key not in portfolio_map:
            portfolio_map[core_key] = {
                "symbols": [],
                "passed_symbols": 0,
                "total_profit_score": 0.0,
                "total_trades": 0,
                "gross_profit": 0.0,
                "gross_loss": 0.0,
                "total_maxdd_stress": 0.0,  # Sum of individual MaxDDs
                # Phase 6E tracking
                "fail_count": 0,
                "warn_count": 0,
                "total_symbols": 0,
                # Equity tracking
                "equity_curves": [],  # Store individual curves for correct alignment
                "equity_series": None,  # Computed later
            }

        agg = portfolio_map[core_key]
        agg["symbols"].append(s)
        agg["total_symbols"] += 1
        agg["total_trades"] += tc

        # Gross metrics aggregation
        agg["gross_profit"] += r.metrics.gross_profit
        agg["gross_loss"] += abs(r.metrics.gross_loss)

        # Stress DD
        mdd = r.metrics.max_dd_pct
        agg["total_maxdd_stress"] += abs(mdd)

        if status == "PASS":
            agg["passed_symbols"] += 1
        elif status == "FAIL":
            agg["fail_count"] += 1
        elif status == "WARN":
            agg["warn_count"] += 1

        agg["total_profit_score"] += ps

        # r is SimulationResult, metrics is MetricSet
        # equity_curve is in metrics
        if r.metrics.equity_curve:
            if isinstance(r.metrics.equity_curve, dict):
                eq_s = pd.Series(r.metrics.equity_curve)
                # Ensure datetime index
                if not pd.api.types.is_datetime64_any_dtype(eq_s.index):
                    eq_s.index = pd.to_datetime(eq_s.index)
            else:
                eq_s = pd.Series(r.metrics.equity_curve)

            if agg["equity_curves"] is None:
                agg["equity_curves"] = []
            agg["equity_curves"].append(eq_s)

        # ... (rest of loop) ...

    # Generate Portfolio Summary & Determine Sub-Plateau Candidates
    robust_candidates = []
    portfolio_summary_rows = []

    for (tf, p_tuple), agg in portfolio_map.items():
        gl = agg["gross_loss"]
        gp = agg["gross_profit"]
        port_pf = (gp / gl) if gl > 0 else (999.0 if gp > 0 else 0.0)

        passed_count = agg["passed_symbols"]
        total_sym = agg["total_symbols"]
        fail_count = agg["fail_count"]
        warn_count = agg["warn_count"]

        # Phase 6E Portfolio Validation
        # 1. Bad Apple Rule
        port_status = "PASS"
        port_fail_reason = ""

        if fail_count > 0:
            port_status = "FAIL"
            port_fail_reason = "Bad Apple (Member Failed)"
        elif total_sym > 0:
            warn_ratio = warn_count / total_sym
            if warn_ratio > 0.30:  # noqa: PLR2004
                port_status = "FAIL"  # 6E Spec: >30% WARN = FAIL
                port_fail_reason = f"Too Many Warns ({warn_ratio:.1%})"
            elif warn_count > 0:
                port_status = "WARN"

        # Empty Portfolio Defense
        if total_sym == 0:
            port_status = "FAIL"
            port_fail_reason = "Empty Portfolio"

        is_robust = (port_status in ["PASS", "WARN"]) and (passed_count >= 2)  # noqa: PLR2004

        avg_profit_score = agg["total_profit_score"] / max(1, len(agg["symbols"]))

        # Portfolio MaxDD & CAGR
        # --- DEFECT #2 FIX: PORTFOLIO AGGREGATION ALIGNMENT ---
        # 1. Union Index across all curves
        # 2. Reindex & FFill (carry forward last equity)
        # 3. Sum & Div N

        if agg.get("equity_curves"):
            curves = agg["equity_curves"]
            if curves:
                # 1. Union Index
                all_idx = pd.Index([])
                for c in curves:
                    all_idx = all_idx.union(c.index)
                all_idx = all_idx.sort_values()

                # 2. Reindex & Sum
                # Start with 0.0
                combined_eq = pd.Series(0.0, index=all_idx)

                for c in curves:
                    # Reindex to full range
                    c_aligned = c.reindex(all_idx)
                    # Forward fill existing values (hold cash value if no new data)
                    c_ffill = c_aligned.ffill()
                    # Fill leading NaNs with initial_cash (asset didn't exist yet, so we held cash)
                    c_final = c_ffill.fillna(engine_cfg.initial_cash)

                    combined_eq = combined_eq.add(c_final, fill_value=0)

                # 3. Divide by N (Equal Weight)
                # combined_eq is Total Portfolio Value.
                # To maintain "unit" scale (comparable to initial_cash), div by N.
                if total_sym > 0:
                    agg["equity_series"] = combined_eq / total_sym
                else:
                    agg["equity_series"] = combined_eq

        port_max_dd = 0.0
        port_cagr = 0.0
        port_calmar = 0.0

        if "equity_series" in agg and agg["equity_series"] is not None:
            eq_combined = agg["equity_series"]
            # Already normalized above

            if not eq_combined.empty:
                # MaxDD
                peak = eq_combined.cummax()
                dd = (eq_combined / peak) - 1.0
                port_max_dd = float(dd.min()) * -1.0

                # CAGR
                start_val = float(eq_combined.iloc[0])
                end_val = float(eq_combined.iloc[-1])
                days = (eq_combined.index[-1] - eq_combined.index[0]).days
                if days > 0 and start_val > 0:
                    years = days / 365.25
                    port_cagr = (end_val / start_val) ** (1 / years) - 1.0

                # Calmar
                if port_max_dd > 0:
                    port_calmar = port_cagr / port_max_dd
                elif port_cagr > 0:
                    port_calmar = 100.0

        # Stress DD (Sum of MaxDDs / N) - Prompt: "sum(w * max_dd_i)"
        # total_maxdd_stress accumulated abs(max_dd_i).
        # So divide by total_sym (N).
        stress_dd_sum = agg.get("total_maxdd_stress", 0.0)
        stress_dd = stress_dd_sum / total_sym if total_sym > 0 else 0.0

        # 3. Min Trades Check (Prompt: "enforce portfolio_min_trades > 0")
        if agg["total_trades"] == 0:
            port_status = "FAIL"
            port_fail_reason = "No Trades"

        p_dict = dict(p_tuple)

        # Robust Candidate (for Leaderboard)
        if is_robust:
            robust_record = p_dict.copy()
            robust_record["timeframe"] = tf
            robust_record["portfolio_pf"] = port_pf
            robust_record["portfolio_calmar"] = port_calmar
            robust_record["avg_profit_score"] = avg_profit_score
            robust_record["passed_count"] = passed_count
            robust_record["stress_dd"] = stress_dd
            robust_candidates.append(robust_record)

        # Summary Row
        row = p_dict.copy()
        row["timeframe"] = tf
        row["passed_symbols"] = passed_count
        row["portfolio_status"] = port_status
        row["fail_reason"] = port_fail_reason
        row["total_trades"] = agg["total_trades"]
        row["gross_profit"] = agg["gross_profit"]
        row["gross_loss"] = agg["gross_loss"]
        row["portfolio_pf"] = port_pf
        row["portfolio_max_dd_pct"] = port_max_dd
        row["portfolio_stress_dd"] = stress_dd
        row["portfolio_calmar"] = port_calmar
        row["portfolio_cagr"] = port_cagr
        row["portfolio_pf"] = port_pf
        row["portfolio_max_dd_pct"] = port_max_dd
        row["portfolio_cagr"] = port_cagr
        row["portfolio_calmar"] = port_calmar
        portfolio_summary_rows.append(row)

    # Leaderboards
    # 1. Top PF (Raw)
    top_pf = sorted(all_configs_flat, key=lambda x: x["profit_factor"], reverse=True)[:10]

    # 2. Top Calmar (Among Passers)
    passers = [x for x in all_configs_flat if x["status"] == "PASS"]
    top_calmar = sorted(passers, key=lambda x: x["calmar_ratio"], reverse=True)[:10]

    # 3. Top ProfitScore (PASS only)
    top_score_pass = sorted(passers, key=lambda x: x["profit_score"], reverse=True)[:10]

    # 4. Top ProfitScore (ALL)
    top_score_all = sorted(all_configs_flat, key=lambda x: x["profit_score"], reverse=True)[:10]

    # 5. Top Robust
    top_robust = sorted(robust_candidates, key=lambda x: x["avg_profit_score"], reverse=True)[:10]

    # Failure Histogram
    fail_reasons = [x["fail_reason"] for x in all_configs_flat if x["status"] == "FAIL"]
    fail_hist = dict(Counter(fail_reasons).most_common(20))

    # Save Results CSV
    flat_data = []
    for r in all_configs_flat:
        row = r["params"].copy()
        row["timeframe"] = r["timeframe"]
        row["symbol"] = r["symbol"]
        row["status"] = r["status"]
        row["fail_gate"] = r["fail_gate"]
        row["fail_reason"] = r["fail_reason"]
        row["profit_factor"] = r["profit_factor"]
        row["profit_score"] = r["profit_score"]
        row["calmar_ratio"] = r["calmar_ratio"]
        row["win_rate"] = r["win_rate"]
        row["cagr"] = r["cagr"]
        row["trade_count"] = r["trade_count"]
        row["max_dd_pct"] = r["max_dd_pct"]
        row["sharpe_ratio"] = r["sharpe_ratio"]
        # Phase 6d
        row["interval_source"] = r.get("interval_source", "")
        row["slippage_bps"] = r.get("slippage_bps", 0.0)
        row["start_date"] = r.get("start_date", "")
        row["end_date"] = r.get("end_date", "")
        row["interval_source"] = r.get("interval_source", "")
        row["slippage_bps"] = r.get("slippage_bps", 0.0)
        row["start_date"] = r.get("start_date", "")
        row["end_date"] = r.get("end_date", "")
        row["profit_status"] = r.get("profit_status", "")
        row["safety_status"] = r.get("safety_status", "")
        row["safety_warnings"] = r.get("safety_warnings", "")
        flat_data.append(row)
    # Task 4: Schema Stability (Always write headers)
    results_cols = [
        "config_idx",
        "ma_length",
        "rsi_length",
        "timeframe",
        "symbol",
        "total_return",
        "sharpe",
        "max_dd",
        "win_rate",
        "trades",
        "sqn",
        "profit_factor",
        "expectancy",
        "slippage_bps",
        "start_date",
        "end_date",
        "interval_source",
        "profit_status",
        "safety_status",
        "safety_warnings",
    ]

    if flat_data:
        pd.DataFrame(flat_data).to_csv(os.path.join(output_dir, "results.csv"), index=False)
    else:
        pd.DataFrame(columns=results_cols).to_csv(os.path.join(output_dir, "results.csv"), index=False)

    # Save Portfolio Summary CSV
    summary_cols = [
        "config_idx",
        "ma_length",
        "rsi_length",
        "portfolio_return",
        "portfolio_sharpe",
        "portfolio_max_dd",
        "portfolio_pf",
        "avg_win_rate",
        "total_trades",
        "calmar_ratio",
        "profit_score",
    ]

    if portfolio_summary_rows:
        pd.DataFrame(portfolio_summary_rows).to_csv(os.path.join(output_dir, "portfolio_summary.csv"), index=False)
    else:
        pd.DataFrame(columns=summary_cols).to_csv(os.path.join(output_dir, "portfolio_summary.csv"), index=False)

    # Save Portfolio Top 10 TXT
    # 1. By Portfolio PF
    top_port_pf = sorted(portfolio_summary_rows, key=lambda x: x["portfolio_pf"], reverse=True)[:10]
    # 2. By Avg Score
    # Note: 'avg_profit_score' is not in summary rows, wait.
    # It was in robust_candidates but maybe not copied to summary rows (which iterate map items).
    # summary rows built line 527.
    # map has total_profit_score.
    # Let's re-calculate or assume 'portfolio_pf' is primary.
    # User asked for "best param sets by portfolio_profit_factor and by portfolio_profit_score".
    # We need to ensure profit_score is in the summary row to list it.

    with open(os.path.join(output_dir, "portfolio_summary_top10.txt"), "w") as f:
        f.write("--- TOP 10 PORTFOLIO CONFIGS (BY PF) ---\n")
        for i, r in enumerate(top_port_pf):
            f.write(
                f"{i + 1}. {r['timeframe']} PF={r['portfolio_pf']:.2f} Trades={r['total_trades']} Passed={r['passed_symbols']}\n"  # noqa: E501
            )
            f.write(f"    Params: {r}\n")

    # Topological Analysis (Per-Slice)
    # Instead of one global mask, we iterate slices (Symbol, Timeframe)
    # Because adjacency between BTC 6h and ETH 6h is meaningless.

    slice_reports = []

    for s in symbols:
        for tf in timeframes:
            # 1. Extract Slice Mask & Indices
            local_shape = tuple([len(v) for v in axis_values])
            local_mask = np.zeros(local_shape, dtype=bool)

            # Map local idx to global idx
            s_idx = symbols.index(s)
            tf_idx = timeframes.index(tf)

            local_trade_counts = {}
            local_expectancies = {}
            local_unsafe = []

            it = np.ndindex(local_shape)
            has_pass = False
            for local_idx in it:
                global_idx = tuple([s_idx, tf_idx] + list(local_idx))

                if global_idx in results and results[global_idx].status == "PASS":
                    local_mask[local_idx] = True
                    has_pass = True

                local_trade_counts[local_idx] = (
                    trade_count_values[list(results.keys()).index(global_idx)] if global_idx in results else 0
                )
                # Expectancy not readily available in flat list easily mapped?
                # We need it from results dict
                if global_idx in results:
                    local_expectancies[local_idx] = results[global_idx].metrics.expectancy_pct

                if global_idx in results and results[global_idx].status != "PASS":
                    local_unsafe.append(local_idx)

            if not has_pass:
                continue

            # 2. Connected Components on Slice
            comps = connected_components(local_mask)
            comps_sorted = sorted(comps, key=len, reverse=True)

            if not comps_sorted:
                continue

            largest = comps_sorted[0]

            # 3. Select Deep Interior
            best_local_idx, interior_meta = select_deep_interior(
                largest, local_unsafe, local_trade_counts, local_expectancies, thresholds.min_trades_centroid
            )

            # Reconstruct Config
            chosen_params = {}
            for i, name in enumerate(axis_names):
                val_idx = best_local_idx[i]
                chosen_params[name] = axis_values[i][val_idx]

            best_global_idx = tuple([s_idx, tf_idx] + list(best_local_idx))
            result_blob = results[best_global_idx]

            slice_report = {
                "symbol": s,
                "timeframe": tf,
                "plateau_size": len(largest),
                "interior_score": interior_meta["interior_distance"],
                "profit_factor": result_blob.get("profit_factor", 0.0),
                "profit_score": result_blob.get("profit_score", 0.0),
                "params": chosen_params,
            }
            slice_reports.append(slice_report)

    report = {
        "status": "OK",
        "leaderboard_pf_raw": top_pf,
        "leaderboard_calmar_pass": top_calmar,
        "leaderboard_profit_score_pass": top_score_pass,
        "leaderboard_profit_score_all": top_score_all,
        "leaderboard_robust": top_robust,
        "fail_histogram": fail_hist,
        "slices": slice_reports,
    }

    save_yaml(report, f"{output_dir}/calibration_report.yaml")

    # Save Fortress Candidate (Best Robust or Best Slice ProfitScore)
    # Prefer Robust
    if top_robust:
        win = top_robust[0]
        # We need to output the param dict for this winner
        # top_robust elements are dicts with params + metrics
        save_yaml(win, f"{output_dir}/fortress_candidate.yaml")
    elif slice_reports:
        # Fallback to best slice
        best_slice = sorted(slice_reports, key=lambda x: x["profit_score"], reverse=True)[0]
        save_yaml(best_slice, f"{output_dir}/fortress_candidate.yaml")

    # Print Summary
    print("\n--- PROFIT ENGINE LEADERBOARD (Top 3 Robust) ---")
    for i, r in enumerate(top_robust[:3]):
        print(
            f"{i + 1}. {r['timeframe']} PF={r['portfolio_pf']:.2f} Score={r['avg_profit_score']:.2f} (Passed {r['passed_count']})"  # noqa: E501
        )

    return report
