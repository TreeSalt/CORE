import json
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

from mantis_core.portfolio_benchmark import (
    compute_alpha_metrics,
    compute_equal_weight_benchmark,
)
from mantis_core.reporting import save_run_metadata
from mantis_core.utils import safe_to_csv


def generate_regime_report(  # noqa: PLC0415, PLR0912, PLR0913, PLR0915
    regime_log: List[Dict[str, Any]],
    equity_curve: pd.DataFrame,
    outdir: Path,
    periods_per_year: int,
    close_prices_df: pd.DataFrame | None = None,
    initial_cash: float = 100_000.0,
    metadata_config: Dict[str, Any] | None = None,
    total_trades: int = 0,
    trades: List[Any] | None = None,
    extra_metadata: Dict[str, Any] | None = None,
) -> None:  # noqa: PLR0912, PLR0915, PLC0415
    """
    Generate performance matrix per regime.
    Phase 9D: includes safety state metrics, drawdown date range,
    worst 1-day return, and exposure cap events.
    Vanguard Effective: adds benchmark comparison.
    """
    # Task 5: Mandatory Trace (Empty)
    if not regime_log:
        trace_headers = [
            "timestamp",
            "regime",
            "trend_dir",
            "vol_scalar",
            "safety_rate",
            "final_leverage",
            "top_weights",
            "final_weights_hash",
            "avg_corr",
            "corr_dropped_count",
            "safety_state",
        ]
        # Ensure headers are written
        safe_to_csv(pd.DataFrame(columns=trace_headers), outdir / "router_trace.csv", index=False)

        # Task 5: RUN_METADATA.json (Standarized)
        base_extra = {"periods_per_year": periods_per_year, "note": "EMPTY_RUN_NO_TRADES"}
        if extra_metadata:
            base_extra.update(extra_metadata)
        save_run_metadata(outdir, config={}, extra=base_extra)
        return

    # Convert log to DF
    regime_df = pd.DataFrame(regime_log)
    if not regime_df.empty:
        regime_df["timestamp"] = pd.to_datetime(regime_df["timestamp"])
        regime_df = regime_df.set_index("timestamp")
    else:
        regime_df = pd.DataFrame(columns=["timestamp"]).set_index("timestamp")

    # Ensure equity curve has returns
    if "equity" in equity_curve.columns:
        equity_curve["returns"] = equity_curve["equity"].pct_change().fillna(0)

    # Merge: forward-fill regime label to daily equity curve
    # Only join columns from regime_df that don't already exist in equity_curve
    join_cols = ["confirmed_regime"]
    for col in ["safety_state", "dd_asof", "ath_asof", "overlay_reason"]:
        if col in regime_df.columns and col not in equity_curve.columns:
            join_cols.append(col)

    merged = equity_curve.join(regime_df[join_cols], how="left")
    merged["regime"] = merged["confirmed_regime"].ffill().fillna("UNKNOWN")

    # Group by Regime
    stats = {}
    for regime, group in merged.groupby("regime"):
        if regime == "UNKNOWN":
            continue

        ret = group["returns"]
        total_ret = (1 + ret).prod() - 1.0
        n_days = len(ret)

        mean_ret = ret.mean()
        std_ret = ret.std()
        sharpe = 0.0
        if std_ret > 1e-9:  # noqa: PLR2004
            sharpe = (mean_ret / std_ret) * (periods_per_year**0.5)

        cum = (1 + ret).cumprod()
        peak = cum.cummax()
        dd = (cum / peak) - 1.0
        # 1. Global DD seen during this regime
        # `dd` is the global drawdown series (from global ATH)
        # We want the worst global DD that occurred on any day labeled with this regime.
        max_dd_global = dd.min()

        # 2. Segment Drawdown
        # For each contiguous block of this regime, calculate DD relative to the block start.
        # Then take the worst of those.
        segment_dds = []

        # Identify contiguous blocks
        # Create a boolean mask for this regime
        is_regime = merged["regime"] == regime
        # Identify changes to find blocks
        block_ids = (is_regime != is_regime.shift()).cumsum()

        # Filter only blocks that ARE this regime
        regime_blocks = merged[is_regime].groupby(block_ids[is_regime])

        for _, block in regime_blocks:
            if block.empty:
                continue
            # Calculate DD relative to block start price (or peak within block?)
            # Usually "Segment DD" implies "Loss since entering".
            # So reference price is Price[Start].
            # Actually, standard is Peak-to-Trough WITHIN the segment.
            # So re-calculate cum returns starting at 1.0 for the block.
            block_ret = block["returns"]
            block_cum = (1 + block_ret).cumprod()
            block_peak = block_cum.cummax()
            block_dd = (block_cum / block_peak) - 1.0
            segment_dds.append(block_dd.min())

        max_dd_segment = min(segment_dds) if segment_dds else 0.0

        stats[regime] = {
            "bars_in_regime": int(n_days),
            "total_return_pct": float(round(total_ret * 100, 2)),
            "sharpe_ratio": float(round(sharpe, 2)),
            "max_drawdown_pct_global": float(round(max_dd_global * 100, 2)),
            "within_segment_max_drawdown_pct": float(round(max_dd_segment * 100, 2)),
        }

    # Write regime_matrix.json
    report_path = outdir / "regime_matrix.json"
    with open(report_path, "w") as f:
        json.dump(stats, f, indent=2, sort_keys=True)

    # Write regime_log.csv (now includes safety columns)
    safe_to_csv(regime_df, outdir / "regime_log.csv")

    # Write router_trace.csv (Task G: full decision trace)
    # MISSION v4.7.2: Also emit DECISION_TRACE.json (Mandated)
    trace_cols = [
        "timestamp",
        "regime",
        "trend_dir",
        "vol_scalar",
        "safety_rate",
        "final_leverage",
        "top_weights",
        "final_weights_hash",
        "avg_corr",
        "corr_dropped_count",
        "safety_state",
    ]

    # Prepare trace DF safely (avoid duplicate timestamp if index named same)
    trace_df = regime_df.reset_index()

    # Mandate 3: Map regime label to 'regime' for trace consistency
    if "confirmed_regime" in trace_df.columns and "regime" not in trace_df.columns:
        trace_df["regime"] = trace_df["confirmed_regime"]

    # Ensure all columns exist
    for c in trace_cols:
        if c not in trace_df.columns:
            trace_df[c] = ""

    # JSON Encode top_weights for machine readability
    if "top_weights" in trace_df.columns:
        trace_df["top_weights"] = trace_df["top_weights"].apply(
            lambda x: json.dumps(x) if isinstance(x, (dict, list)) else x
        )

    safe_to_csv(trace_df[trace_cols], outdir / "router_trace.csv", index=False)
    
    # MISSION v4.7.2: Emitting Mandated REGIME_DECISION_TRACE.json
    trace_json = trace_df[trace_cols].to_dict(orient="records")
    with open(outdir / "REGIME_DECISION_TRACE.json", "w") as f:
        json.dump(trace_json, f, indent=2, default=str)
    print(f"🛡️  Artifact Secured: REGIME_DECISION_TRACE.json ({len(trace_json)} records)")

    # Task 5: RUN_METADATA.json (Standardized)
    final_config = metadata_config or {}
    final_config.update({"regime_settings": "derived_from_log", "initial_cash": initial_cash})
    
    final_extra = {
        "n_regime_changes": len(regime_df),
        "total_bars": len(equity_curve),
        "initial_cash": initial_cash,
        "periods_per_year": periods_per_year,
    }
    if extra_metadata:
        final_extra.update(extra_metadata)

    save_run_metadata(
        outdir,
        config=final_config,
        extra=final_extra,
    )

    # Write full merged equity_regime_curve.csv
    safe_to_csv(merged, outdir / "equity_regime_curve.csv")

    # ── Council Artifacts ──
    all_returns = equity_curve.get("returns", pd.Series(dtype=float))
    if all_returns.empty and "equity" in equity_curve.columns:
        all_returns = equity_curve["equity"].pct_change().fillna(0)

    total_ret = (1 + all_returns).prod() - 1.0
    mean_r = all_returns.mean()
    std_r = all_returns.std()
    sharpe = (mean_r / std_r) * (periods_per_year**0.5) if std_r > 1e-9 else 0.0  # noqa: PLR2004
    cum = (1 + all_returns).cumprod()
    dd_series = (cum / cum.cummax()) - 1.0
    max_dd = dd_series.min()
    n_trades = len(regime_log)
    if trades:
        from mantis_core.metrics import profit_factor  # noqa: PLC0415
        pf = profit_factor(trades)
    else:
        # Fallback (NOT RECOMMENDED for Strategy Truth)
        pf = (
            abs(all_returns[all_returns > 0].sum() / all_returns[all_returns < 0].sum())
            if all_returns[all_returns < 0].sum() != 0
            else 999.0
        )

    # MISSION v4.5.290: Worst 1-day return (resample to daily first)
    if "equity" in equity_curve.columns and not equity_curve.empty:
        daily_eq = equity_curve["equity"].resample("1D").last().ffill()
        daily_ret = daily_eq.pct_change().fillna(0)
        worst_1d = float(daily_ret.min())
    else:
        worst_1d = float(all_returns.min()) if len(all_returns) > 0 else 0.0

    # Max DD date range (peak → trough)
    trough_idx = dd_series.idxmin() if len(dd_series) > 0 else None
    if trough_idx is not None:
        # Peak is the last ATH before the trough
        cum_to_trough = cum.loc[:trough_idx]
        peak_idx = cum_to_trough.idxmax()
        dd_date_range = {
            "peak_ts": str(peak_idx),
            "trough_ts": str(trough_idx),
        }
    else:
        dd_date_range = {"peak_ts": "", "trough_ts": ""}

    # Safety state time counts
    safety_counts = {}
    if "safety_state" in equity_curve.columns:
        safety_counts = equity_curve["safety_state"].value_counts().to_dict()

    # Exposure cap events
    exposure_cap_events = 0
    if "safety_state" in equity_curve.columns:
        exposure_cap_events = int((equity_curve["safety_state"] != "NORMAL").sum())

    overall = {
        "total_return_pct": round(total_ret * 100, 2),
        "sharpe_ratio": round(sharpe, 2),
        "overall_max_drawdown_pct": round(max_dd * 100, 2),
        "profit_factor": round(float(pf), 2),
        "rebalance_events": n_trades,
        "trade_count": total_trades,
        "total_bars": len(equity_curve),
        "worst_1d_return_pct": round(worst_1d * 100, 4),
        "max_drawdown_date_range": dd_date_range,
        "time_in_safety_states": safety_counts,
        "exposure_cap_events": exposure_cap_events,
    }

    # ── Benchmark (Vanguard Effective: Task 6) ──
    benchmark_metrics: Dict[str, Any] = {}
    alpha_metrics: Dict[str, Any] = {}
    if close_prices_df is not None and not close_prices_df.empty:
        benchmark_metrics = compute_equal_weight_benchmark(close_prices_df, periods_per_year, initial_cash)
        bench_equity = benchmark_metrics.pop("benchmark_equity_series", pd.Series(dtype=float))

        if "equity" in equity_curve.columns and not bench_equity.empty:
            port_equity = equity_curve["equity"]
            alpha_metrics = compute_alpha_metrics(port_equity, bench_equity, periods_per_year=periods_per_year)

    overall["benchmark"] = {
        **{k: v for k, v in benchmark_metrics.items()},
        **alpha_metrics,
    }

    # PORTFOLIO_SUMMARY.json
    summary_json = {
        "overall": overall,
        "per_regime": stats,
    }
    with open(outdir / "PORTFOLIO_SUMMARY.json", "w") as f:
        json.dump(summary_json, f, indent=2, sort_keys=True, default=str)

    # SUMMARY.md
    lines = [
        "# Portfolio Backtest Summary",
        "",
        "## Overall Metrics",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Total Return | {overall['total_return_pct']:.2f}% |",
        f"| Sharpe Ratio | {overall['sharpe_ratio']:.2f} |",
        f"| Overall Max Drawdown | {overall['overall_max_drawdown_pct']:.2f}% |",
        f"| Profit Factor | {overall['profit_factor']:.2f} |",
        f"| Rebalance Events | {overall['rebalance_events']} |",
        f"| Trade Count | {overall['trade_count']} |",
        f"| Total Bars | {overall['total_bars']} |",
        f"| Worst 1-Day | {overall['worst_1d_return_pct']:.4f}% |",
        f"| DD Peak→Trough | {dd_date_range['peak_ts']} → {dd_date_range['trough_ts']} |",
        f"| Exposure Cap Events | {overall['exposure_cap_events']} |",
        "",
    ]

    # Benchmark section
    bench = overall.get("benchmark", {})
    if bench:
        lines += [
            "## Benchmark Comparison (Equal-Weight B&H)",
            "",
            "| Metric | Value |",
            "|--------|-------|",
            f"| Benchmark Return | {bench.get('benchmark_total_return_pct', 0):.2f}% |",
            f"| Benchmark Sharpe | {bench.get('benchmark_sharpe_ratio', 0):.2f} |",
            f"| Benchmark Max DD | {bench.get('benchmark_max_drawdown_pct', 0):.2f}% |",
            f"| Excess Return | {bench.get('excess_return_pct', 0):.2f}% |",
            f"| Tracking Error | {bench.get('tracking_error', 0):.4f} |",
            f"| Information Ratio | {bench.get('information_ratio', 0):.2f} |",
            f"| Max DD Diff | {bench.get('max_dd_diff_pct', 0):.2f}% |",
            "",
        ]

    lines += [
        "## Safety State Distribution",
        "",
        "| State | Bars |",
        "|-------|------|",
    ]
    for state, count in safety_counts.items():
        lines.append(f"| {state} | {count} |")

    lines += [
        "",
        "## Per-Regime Performance",
        "",
        "| Regime | Bars | Return | Sharpe | DD (Global) | DD (Segment) |",
        "|--------|------|--------|--------|-------------|--------------|",
    ]
    for regime, s in stats.items():
        lines.append(
            f"| {regime} | {s['bars_in_regime']} | {s['total_return_pct']:.2f}% | "
            f"{s['sharpe_ratio']:.2f} | {s['max_drawdown_pct_global']:.2f}% | {s['within_segment_max_drawdown_pct']:.2f}% |"  # noqa: E501
        )
    lines.append("")

    with open(outdir / "SUMMARY.md", "w") as f:
        f.write("\n".join(lines))
