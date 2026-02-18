from __future__ import annotations

import math
from typing import Any, Dict, List, Tuple

import pandas as pd

from antigravity_harness.data import load_ohlc
from antigravity_harness.engine import run_backtest
from antigravity_harness.metrics import compute_metrics
from antigravity_harness.models import GateResult, SimulationContext
from antigravity_harness.profiles import get_profile

# GateResult moved to models.py for Pillar 1 (Typed Sovereignty)

# GateResult moved to models.py for Pillar 1 (Typed Sovereignty)


def _calc_annual_vol(df: pd.DataFrame, periods: int) -> float:
    if len(df) < 30:  # noqa: PLR2004
        return 0.0
    # Log returns
    rets = df["Close"].pct_change().dropna()
    # Apply correct annualization
    vol = rets.std() * math.sqrt(periods)
    return float(vol)


def _run_sim(ctx: SimulationContext) -> Dict[str, Any]:  # noqa: PLR0915
    # Phase 2: Context Injection
    strategy = ctx.strategy
    params = ctx.params
    data_cfg = ctx.data_cfg
    engine_cfg = ctx.engine_cfg
    symbol = ctx.symbol
    start = ctx.start
    end = ctx.end
    override_df = ctx.override_df

    # Load Data
    try:
        df = override_df.copy() if override_df is not None else load_ohlc(symbol, start, end, data_cfg)
    except Exception as e:
        raise ValueError(f"Data Load Error: {e}") from e

    if df.empty:
        return {}

    # Data Integrity Pre-Check (NaN / Zero-Volume Guard)
    ohlc_cols = [c for c in ("Open", "High", "Low", "Close") if c in df.columns]
    nan_counts = df[ohlc_cols].isna().sum()
    bad_cols = nan_counts[nan_counts > 0]
    if not bad_cols.empty:
        raise ValueError(f"DATA_INTEGRITY: NaN detected in OHLC columns: {dict(bad_cols)}")

    if "Volume" in df.columns and (df["Volume"] == 0).all():
        raise ValueError("DATA_INTEGRITY: All volume bars are zero (zero-volume saturation)")

    # Physics is already injected in ctx via Builder
    periods_year = engine_cfg.periods_per_year
    vol = _calc_annual_vol(df, periods=periods_year)

    prepared = strategy.prepare_data(df, params, intelligence=ctx.intelligence)
    res = run_backtest(df, prepared, params, engine_cfg, debug=ctx.debug, out_dir=ctx.out_dir)
    m = res.metrics.model_dump()
    m["annualized_vol"] = vol

    # Equity Curve & Trades serialization
    ec_series = res.equity_curve.ffill().fillna(engine_cfg.initial_cash)
    m["equity_curve"] = {str(k): float(v) for k, v in ec_series.items()}

    # Gross Metrics (for Portfolio Aggregation)
    gp = sum(t.pnl_abs for t in res.trades if t.pnl_abs > 0)
    gl = sum(t.pnl_abs for t in res.trades if t.pnl_abs <= 0)
    m["gross_profit"] = float(gp)
    m["gross_loss"] = float(
        gl
    )  # Ensure negative or positive? Convention: GL usually positive magnitude or negative value?
    # Logic in calibration.py: agg["gross_loss"] += abs(r.get("gross_loss"))
    # So here can be negative.

    trade_list = []
    for t in res.trades:
        td = t.model_dump()
        td["entry_time"] = str(td["entry_time"])
        td["exit_time"] = str(td["exit_time"])
        trade_list.append(td)

    m["trades"] = trade_list

    # --- DEFECT #1 FIX: WALK-FORWARD LEAKAGE PREVENTION ---
    # If using override_df (snapshot) AND explicit start/end, we MUST filter metrics to the eval window.
    # The backtest ran on Warmup + Eval. We must discard Warmup metrics.
    if override_df is not None and start and end:
        # Convert to tz-naive for consistent comparison
        s_dt = pd.to_datetime(start).tz_localize(None)
        e_dt = pd.to_datetime(end).tz_localize(None)

        # 1. Filter Trades by Exit Time (Evaluation Window Only)
        trades_eval = []
        trade_list_eval = []
        for t in res.trades:
            t_exit = pd.to_datetime(t.exit_time).tz_localize(None)
            if s_dt <= t_exit <= e_dt:
                trades_eval.append(t)
                td = t.model_dump()
                td["entry_time"] = str(td["entry_time"])
                td["exit_time"] = str(td["exit_time"])
                trade_list_eval.append(td)

        # 2. Filter Equity Curve
        ec_idx = pd.to_datetime(ec_series.index).tz_localize(None)
        ec_series.index = ec_idx
        # Filter strictly
        # Ensure we don't crash if empty
        equity_eval_raw = ec_series.loc[(ec_series.index >= s_dt) & (ec_series.index <= e_dt)]

        # If empty (no bars in eval window), return empty safe state
        if equity_eval_raw.empty:
            return {}

        # 3. Recompute Metrics on Filtered Data
        new_metrics = compute_metrics(equity_eval_raw, trades_eval, periods_per_year=periods_year, symbol=symbol)
        m.update(new_metrics)

        # 4. Recompute Gross Metrics
        gp_eval = sum(t.pnl_abs for t in trades_eval if t.pnl_abs > 0)
        gl_eval = sum(t.pnl_abs for t in trades_eval if t.pnl_abs <= 0)
        m["gross_profit"] = float(gp_eval)
        m["gross_loss"] = float(gl_eval)

        # 5. Recalc Vol on Eval Window
        try:
            df_eval = df.loc[(df.index >= s_dt) & (df.index <= e_dt)]
            # Use same periods_year determined earlier
            m["annualized_vol"] = _calc_annual_vol(df_eval, periods=periods_year)
        except Exception:
            m["annualized_vol"] = 0.0

        # 6. Update Serialized Traces
        m["equity_curve"] = {str(k): float(v) for k, v in equity_eval_raw.items()}
        m["trades"] = trade_list_eval

        if res.trace is not None and not res.trace.empty:
            tr = res.trace
            tr_eval = tr[(tr["timestamp"] >= s_dt) & (tr["timestamp"] <= e_dt)]
            m["_trace"] = tr_eval

    if "_trace" not in m and res.trace is not None and not res.trace.empty:
        m["_trace"] = res.trace

    return m


def evaluate_gates(ctx: SimulationContext) -> List[GateResult]:  # noqa: PLR0912
    results = []

    # 1. Profile Loading
    try:
        profile = get_profile(ctx.gate_profile)
    except Exception as e:
        return [GateResult(gate="PROFILE_ERROR", status="FAIL", reason=str(e))]

    # 2. Run Sim
    try:
        # Phase 2: Apply profile slippage (no silent defaults)
        local_engine_cfg = ctx.engine_cfg.model_copy(
            update={"slippage_per_side": float(profile.slippage_bps) / 10000.0}
        )
        sim_ctx = ctx.model_copy(update={"engine_cfg": local_engine_cfg})

        m_baseline = _run_sim(sim_ctx)

        # Surface applied slippage for audit
        m_baseline["slippage_bps_applied"] = profile.slippage_bps

    except ValueError as e:
        # DATA INTEGRITY FAIL (NON-DOWNGRADABLE)
        return [GateResult(gate="GATE_DATA_INTEGRITY", status="FAIL", reason=str(e))]
    except Exception as e:
        return [GateResult(gate="GATE_CRASH", status="FAIL", reason=f"Backtest Crash: {e}")]

    if not m_baseline:
        return [GateResult(gate="GATE_NO_DATA", status="FAIL", reason=f"No Data Coverage for {ctx.symbol}")]

    # Base Metrics
    vol = m_baseline.get("annualized_vol", 0.0)
    pf = m_baseline.get("profit_factor", 0.0)
    trades = m_baseline.get("trade_count", 0)
    max_dd = m_baseline.get("max_dd_pct", 0.0)

    # Extract Trace
    trace_df = m_baseline.get("_trace")

    # 3. Misclassification Defense (NON-DOWNGRADABLE)
    if vol < profile.min_vol_annual:
        return [
            GateResult(
                gate="GATE_MISCLASSIFICATION",
                status="FAIL",
                reason=f"Vol {vol:.2f} < Min {profile.min_vol_annual:.2f}",
                metrics=m_baseline,
                trace=trace_df,
            )
        ]

    # 4. Profit Gates (FAIL only)
    if trades < profile.min_trades_window:
        results.append(
            GateResult(
                gate="GATE_MIN_TRADES",
                status="FAIL",
                reason=f"Trades {trades} < {profile.min_trades_window}",
                metrics=m_baseline,
                trace=trace_df,
            )
        )
    else:
        results.append(
            GateResult(
                gate="GATE_MIN_TRADES", status="PASS", reason=f"Trades {trades} OK", metrics=m_baseline, trace=trace_df
            )
        )

    if pf < profile.min_pf_profit:
        results.append(
            GateResult(
                gate="GATE_PROFIT_FACTOR",
                status="FAIL",
                reason=f"PF {pf:.2f} < {profile.min_pf_profit}",
                metrics=m_baseline,
                trace=trace_df,
            )
        )
    else:
        results.append(
            GateResult(
                gate="GATE_PROFIT_FACTOR", status="PASS", reason=f"PF {pf:.2f} OK", metrics=m_baseline, trace=trace_df
            )
        )

    # 3.3: Sharpe Gate (PROFIT)
    sharpe = m_baseline.get("sharpe_ratio", 0.0)
    # Only enforce if profile requires it (>0)
    if profile.min_sharpe_profit > 0.0 and sharpe < profile.min_sharpe_profit:
        results.append(
            GateResult(
                gate="GATE_SHARPE",
                status="FAIL",
                reason=f"Sharpe {sharpe:.2f} < {profile.min_sharpe_profit}",
                metrics=m_baseline,
                trace=trace_df,
            )
        )
    else:
        results.append(
            GateResult(
                gate="GATE_SHARPE", status="PASS", reason=f"Sharpe {sharpe:.2f} OK", metrics=m_baseline, trace=trace_df
            )
        )

    # 5. Safety Gates (PASS/WARN/FAIL)
    if max_dd > profile.max_dd_fail:  # 0.40 for Crypto
        results.append(
            GateResult(
                gate="GATE_MAX_DD",
                status="FAIL",
                reason=f"DD {max_dd:.1%} > FAIL {profile.max_dd_fail:.1%}",
                metrics=m_baseline,
                trace=trace_df,
            )
        )
    elif max_dd > profile.max_dd_warn:  # 0.25 for Crypto
        results.append(
            GateResult(
                gate="GATE_MAX_DD",
                status="WARN",
                reason=f"DD {max_dd:.1%} > WARN {profile.max_dd_warn:.1%}",
                metrics=m_baseline,
                trace=trace_df,
            )
        )
    else:
        results.append(
            GateResult(
                gate="GATE_MAX_DD", status="PASS", reason=f"DD {max_dd:.1%} OK", metrics=m_baseline, trace=trace_df
            )
        )

    # 6. Zombie Strategy (NON-DOWNGRADABLE)
    ts = m_baseline.get("trades", [])
    if ts:
        last_t_str = ts[-1]["exit_time"]
        last_t = pd.to_datetime(last_t_str).tz_localize(None)
        req_end = pd.to_datetime(ctx.end).tz_localize(None)

        # Check gap
        days_gap = (req_end - last_t).days
        if days_gap > 30:  # noqa: PLR2004
            results.append(
                GateResult(
                    gate="GATE_ZOMBIE",
                    status="FAIL",
                    reason=f"Last trade {days_gap}d ago (>30d)",
                    metrics=m_baseline,
                    trace=trace_df,
                )
            )
        else:
            results.append(
                GateResult(gate="GATE_ZOMBIE", status="PASS", reason="Active", metrics=m_baseline, trace=trace_df)
            )

    return results


def _status_from_gate_results(gate_results: List[GateResult]) -> Tuple[str, str, str, List[str], List[str]]:  # noqa: PLR0912, PLR0915
    """Phase 6E Truth Table Implementation."""
    if not gate_results:
        return "FAIL", "FAIL", "FAIL", [], ["NO_RESULTS"]

    profit_fails = []
    safety_fails = []
    safety_warns = []

    # Analyze gates
    for g in gate_results:
        # Profit Gates (FAIL only)
        # 3.3: Sharpe added as Profit Gate
        if g.gate in ["GATE_MIN_TRADES", "GATE_PROFIT_FACTOR", "GATE_MISCLASSIFICATION", "GATE_SHARPE"]:
            if g.status == "FAIL":
                profit_fails.append(f"{g.gate}: {g.reason}")

        # Safety Gates (PASS/WARN/FAIL)
        # 3.4: Zombie, Data Integrity, Crash -> Hard FAIL
        elif g.gate in [
            "GATE_MAX_DD",
            "GATE_ZOMBIE",
            "GATE_DATA_INTEGRITY",
            "GATE_CRASH",
            "GATE_NO_DATA",
            "GATE_PROFILE_ERROR",
        ]:
            if g.status == "FAIL":
                safety_fails.append(f"{g.gate}: {g.reason}")
            elif g.status == "WARN":
                safety_warns.append(f"{g.gate}: {g.reason}")

        # Catch-all (Unknown gates treated as Safety)
        elif g.status == "FAIL":
            safety_fails.append(f"{g.gate}: {g.reason}")
        elif g.status == "WARN":
            safety_warns.append(f"{g.gate}: {g.reason}")

    # Determine Statuses
    profit_status = "FAIL" if profit_fails else "PASS"

    safety_status = "PASS"
    if safety_fails:
        safety_status = "FAIL"
    elif safety_warns:
        safety_status = "WARN"

    # Overall Truth Table
    overall_status = "PASS"
    if profit_status == "FAIL" or safety_status == "FAIL":
        overall_status = "FAIL"
    elif safety_status == "WARN":
        overall_status = "WARN"

    all_fails = profit_fails + safety_fails
    return profit_status, safety_status, overall_status, safety_warns, all_fails
