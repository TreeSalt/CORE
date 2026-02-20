from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

import antigravity_harness as _ah
from antigravity_harness.autonomy import load_snapshot, save_snapshot, walk_forward_validation
from antigravity_harness.calibration import _run_one, calibrate
from antigravity_harness.certification import run_certification
from antigravity_harness.config import DataConfig, EngineConfig, GateThresholds, StrategyParams, load_yaml, save_yaml
from antigravity_harness.context import SimulationContextBuilder
from antigravity_harness.council import run_council_sweep
from antigravity_harness.data import MarketTape, load_ohlc
from antigravity_harness.emit import unique_signals
from antigravity_harness.engine import run_backtest
from antigravity_harness.gates import evaluate_gates
from antigravity_harness.paths import DATA_DIR, REPO_ROOT, REPORT_DIR, ensure_dirs
from antigravity_harness.portfolio_engine import run_portfolio_backtest_verbose
from antigravity_harness.portfolio_policies import PolicyConfig
from antigravity_harness.portfolio_regime_report import generate_regime_report
from antigravity_harness.portfolio_router import PortfolioRouter, RegimeConfig
from antigravity_harness.portfolio_safety_overlay import SafetyConfig
from antigravity_harness.reality_gap import run_reality_gap
from antigravity_harness.registry import promote_to_staging
from antigravity_harness.reporting import save_artifacts, save_run_metadata
from antigravity_harness.strategies import REGISTRY, STRATEGY_REGISTRY, get_strategy
from antigravity_harness.strategies.catalog import STRATEGY_CATALOG
from antigravity_harness.sweep import run_sweep
from antigravity_harness.utils import infer_periods_per_year, safe_to_csv
from antigravity_harness.zip_verifier import cmd_verify


# HYDRA GUARD: Shell Escape Protection (Vector 36) & String Overflow (Vector 51)
def _sanitize_string(s: str) -> str:
    """Rejects strings containing malicious shell characters or excessive length."""
    # HYDRA GUARD: String Overflow Protection (Vector 51)
    if len(s) > 4096:
        raise ValueError("INPUT_OVERFLOW: String parameter exceeds 4096 characters.")
    
    # HYDRA GUARD: Null Byte Bomb Protection (Vector 111)
    if "\0" in s:
        raise ValueError("SECURITY_VIOLATION: Null byte detected in input.")

    forbidden = {";", "&", "|", ">", "<", "`", "$", "(", ")", "\\", "'", "\"", "*", "?", "[", "]"}
    if any(c in s for c in forbidden):
        raise ValueError(f"SHELL ESCAPE DETECTED: Illegal characters in input '{s}'. Aborting for safety.")
    return s


def cmd_calibrate(args: argparse.Namespace) -> None:  # noqa: PLR0915
    # HYDRA GUARD: Input Sanitization (Vector 36)
    args.symbol = _sanitize_string(args.symbol)
    args.strategy = _sanitize_string(args.strategy)
    args.gate_profile = _sanitize_string(args.gate_profile)
    
    print(f"FORTRESS PROTOCOL: Unicorn-Grade Validity (Profile: {args.gate_profile})")
    out_dir = args.output_dir or str(REPORT_DIR / "artifacts")
    os.makedirs(out_dir, exist_ok=True)

    print("prefetching data...")
    dcfg = DataConfig()
    symbols = [args.symbol] + ["SPY", "TLT", "ARKK", "PFE", "NVDA"]
    # Remove duplicates but keep order
    symbols = list(dict.fromkeys(symbols))

    prefetch_ok = []
    for sym in symbols:
        try:
            # For the target symbol, prefetch using the requested range and interval
            if sym == args.symbol:
                load_ohlc(sym, args.start, args.end, DataConfig(interval=args.interval))
            else:
                load_ohlc(sym, "2016-01-01", "2024-12-31", dcfg)
            print(f"  [x] {sym} cached")
            prefetch_ok.append(sym)
        except Exception as e:
            print(f"  [!] Failed to prefetch {sym}: {e}")
    print(f"PREFETCH COMPLETE: {prefetch_ok}")

    # Handle symbols
    symbol_str = args.symbols if args.symbols else args.symbol
    symbols = [s.strip() for s in symbol_str.split(",")]

    # Handle timeframes override
    timeframes_override = [t.strip() for t in args.timeframes.split(",")] if args.timeframes else None

    # Unified Physics
    engine_cfg = EngineConfig(is_crypto=not args.equity)

    # GOVERNANCE CHECK
    # Enforce research mode for calibrate/validate.
    STRATEGY_REGISTRY.verify_strategy_allowed(args.strategy, mode="research")

    report = calibrate(
        grid_yaml=args.grid,
        output_dir=out_dir,
        strategy_name=args.strategy,
        n_jobs=args.jobs,
        engine_cfg=engine_cfg,  # Pass configured engine
        include_ablation=args.include_ablation,
        include_time_split=args.include_time_split,
        symbols=symbols,
        start=args.start,
        end=args.end,
        interval=args.interval,
        gate_profile=args.gate_profile,  # Pass profile
        timeframes_override=timeframes_override,  # Pass override
        registry=STRATEGY_REGISTRY,
    )

    save_artifacts(out_dir, "calibration_report", report)
    # also print heatmap if available
    print(report.get("heatmap", ""))


def cmd_validate(args: argparse.Namespace) -> None:  # noqa: PLR0915
    print("FORTRESS PROTOCOL: Unicorn-Grade Validity (Phase 6E)")
    out_dir = args.output_dir or str(REPORT_DIR / "artifacts")
    os.makedirs(out_dir, exist_ok=True)

    # Load params
    if args.config:
        cfg = load_yaml(args.config)
        params = StrategyParams(**cfg)
    else:
        # Construct from args or defaults
        p_dict = {
            "ma_length": args.ma_length,
            "rsi_entry": args.rsi_entry,
            "rsi_exit": args.rsi_exit,
            "stop_atr": args.stop_atr,
        }
        params = StrategyParams(**p_dict)

    # HYDRA GUARD: Input Sanitization (Vector 36)
    args.symbol = _sanitize_string(args.symbol)
    args.strategy = _sanitize_string(args.strategy)
    args.gate_profile = _sanitize_string(args.gate_profile)

    # GOVERNANCE CHECK (Fail Fast)
    STRATEGY_REGISTRY.verify_strategy_allowed(args.strategy, mode="research")

    # Use calibration._run_one to ensure Phase 6E gates_6e usage

    # Helper to clean boolean args
    inc_ablation = not args.no_ablation
    inc_time_split = args.time_split

    print(f"Validating {args.symbol} {args.interval} on {args.gate_profile}...")

    # Unified Physics: Engine Config with Asset Class
    engine_cfg = EngineConfig(is_crypto=not args.equity)
    
    # GOVERNANCE CHECK
    STRATEGY_REGISTRY.verify_strategy_allowed(args.strategy, mode="research")

    res = _run_one(
        strategy_name=args.strategy,
        params=params,
        data_cfg=DataConfig(interval=args.interval),
        engine_cfg=engine_cfg,
        thresholds=GateThresholds(),  # Legacy compat
        include_ablation=inc_ablation,
        include_time_split=inc_time_split,
        symbol=args.symbol,
        start=args.start,
        end=args.end,
        gate_profile=args.gate_profile,
        interval=args.interval,
        debug=args.debug,
        out_dir=Path(out_dir),
    )

    # Save Report
    # Extract Trace
    trace_df = res.trace
    if trace_df is not None:
        safe_to_csv(trace_df, f"{out_dir}/router_trace.csv", index=False)

    save_artifacts(out_dir, "validation_report", res.model_dump(), overwrite=True)

    # Phase 10: Run Metadata
    save_run_metadata(
        out_dir,
        config={"strategy": args.strategy, "params": params.model_dump(), "gates": args.gate_profile},
        cmd_args=vars(args),
        extra={"periods_per_year": engine_cfg.periods_per_year},
    )

    print("\n✅ Validation Complete.")
    # Print Results (Phase 6E Format)
    print("-" * 40)
    print(f"OVERALL STATUS: {res.status}")
    print(f"  Profit Status: {res.profit_status}")
    print(f"  Safety Status: {res.safety_status}")
    print(f"  PF: {res.metrics.profit_factor:.2f} | MaxDD: {res.metrics.max_dd_pct:.1%}")
    print("-" * 40)

    # Print Gate Details
    # Print Gate Details
    for g in res.gate_results:
        print(f"[{g.status}] {g.gate}: {g.reason}")

    # If we want exact gate output, we might need to parse fail_reason or look at log
    if res.fail_reason:
        print(f"FAIL REASONS:\n{res.fail_reason}")
    if res.warns:
        print(f"WARNS:\n{'; '.join(res.warns)}")


def cmd_info(args: argparse.Namespace) -> None:
    print("🦅 ANTIGRAVITY: PROJECT HEALTH & STATUS")
    print("-" * 40)

    # 1. Structural Check
    folders = [
        "00_CORE_MANIFEST",
        "antigravity_harness",
        "scripts",
        "tests",
        str(REPORT_DIR.relative_to(REPO_ROOT)),
        str(DATA_DIR.relative_to(REPO_ROOT)),
    ]
    print("CORE STRUCTURE:")
    for f in folders:
        path = REPO_ROOT / f
        exists = path.is_dir()
        status = "🟢" if exists else "🔴"
        print(f"  {status} {f}")

    # 2. Manifest Check
    manifest_path = REPO_ROOT / "docs/ready_to_drop/COUNCIL_CANON.yaml"
    m_icon = "🟢" if manifest_path.exists() else "🔴"
    print(f"CANON: {m_icon} {manifest_path.relative_to(REPO_ROOT)}")

    # 3. Strategy Registry
    print(f"STRATEGY REGISTRY: {len(REGISTRY)} active")
    for s in sorted(REGISTRY.keys()):
        print(f"  - {s}")

    # 4. Data Cache
    cache_path = str(DATA_DIR)
    if os.path.isdir(cache_path):
        files = os.listdir(cache_path)
        print(f"DATA CACHE: {len(files)} objects discovered in '{cache_path}'")
    else:
        print("DATA CACHE: 🔴 Not found")
    print("-" * 40)


def cmd_emit(args: argparse.Namespace) -> None:
    # Resolve params: from config file or defaults?
    # Emit command implies using a specific 'production' config usually.
    # For now, we support loading from --config (YAML) or default params.
    cfg = load_yaml(args.config) if args.config else StrategyParams().__dict__

    # GOVERNANCE CHECK (Live Payload)
    # Emit is typically for production signals. Enforce STRICT "live" check?
    # Or rely on user context? 
    # Let's enforce "live" tier requirements for emit-signals.
    STRATEGY_REGISTRY.verify_strategy_allowed(args.strategy, mode="live")

    json_out = unique_signals(
        strategy_name=args.strategy,
        symbol=args.symbol,
        timeframe=args.timeframe,
        lookback_bars=args.lookback,
        end_date=args.end_date,
        params=cfg,
    )

    if args.output:
        # Save to file
        os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
        with open(args.output, "w") as f:
            f.write(json_out)
        print(f"Signal written to {args.output}")
    else:
        # Print to stdout
        print(json_out)


def cmd_spotcheck(args: argparse.Namespace) -> None:  # noqa: PLR0912, PLR0915
    """
    One-Command Spotcheck: Run a single detailed validaton + raw sim.
    Output: tear_sheet.yaml, equity.csv, trades.csv
    Args: --params "ma_length=150,rsi_entry=65..."
    Args: --params "ma_length=150,rsi_entry=65..."
    """
    print(f"🔬 SPOTCHECK: {args.symbol} {args.interval} | {args.strategy}")
    out_dir = args.output_dir or str(REPORT_DIR / f"spotcheck_{args.symbol}_{args.interval}")
    os.makedirs(out_dir, exist_ok=True)

    # 1. Parse Params String
    # Format: "key=val,key2=val2"
    # We need to map string vals to correct types in StrategyParams
    default_params = StrategyParams()
    param_dict = default_params.model_dump()

    if args.params:
        pairs = args.params.split(",")
        for p in pairs:
            if not p.strip():
                continue
            k, v = p.split("=")
            k = k.strip()
            v = v.strip()

            # Infer type
            if k in param_dict:
                target_type = type(param_dict[k])
                try:
                    val = v.lower() == "true" if isinstance(param_dict[k], bool) else target_type(v)
                    param_dict[k] = val
                except ValueError:
                    print(f"⚠️ Warning: Could not cast param {k}={v} to {target_type}. Keeping default.")

    final_params = StrategyParams(**param_dict)
    print(f"⚙️ Params: {final_params}")

    # GOVERNANCE CHECK (Fail Fast)
    STRATEGY_REGISTRY.verify_strategy_allowed(args.strategy, mode="research")

    # 2. Run Gates (Simulation + Validation)
    start_date = "2020-01-01"  # Default wide range for spot check
    if args.start:
        start_date = args.start

    dcfg = DataConfig(interval=args.interval)
    load_ohlc(args.symbol, start_date, args.end, dcfg)

    strat = get_strategy(args.strategy)
    ctx = (
        SimulationContextBuilder()
        .with_strategy(args.strategy, strat)
        .with_params(final_params)
        .with_data_cfg(dcfg)
        .with_engine_cfg(EngineConfig())
        .with_thresholds(GateThresholds())
        .with_symbol(args.symbol)
        .with_window(start_date, args.end)
        .with_gate_profile(args.gate_profile)
        .with_debug(args.debug)
        .build()
    )
    gate_results = evaluate_gates(ctx)

    # 3. Extract & Save Artifacts
    # We want exact equity curve and trade list
    # gate_results[0] usually has the full history in details

    if not gate_results:
        print("❌ Simulation failed (No gate results returned).")
        return

    main_res_gate = gate_results[0]
    metrics = main_res_gate.metrics

    # Save Tear Sheet (Metrics + Fail Reason)
    fail_reason = ""
    for g in gate_results:
        if not g.passed:
            fail_reason += f"[{g.gate}] {g.reason}; "

    def to_native(v: Any) -> Any:
        if isinstance(v, (np.int64, np.int32, int)):
            return int(v)
        if isinstance(v, (np.float64, np.float32, float)):
            return float(v)
        return v
    tear_sheet = {
        "symbol": args.symbol,
        "interval": args.interval,
        "strategy": args.strategy,
        "params": final_params.model_dump(),
        "status": "PASS" if not fail_reason else "FAIL",
        "fail_reason": fail_reason,
        "metrics": {k: to_native(v) for k, v in metrics.items() if isinstance(v, (int, float, str, np.number))},
    }
    save_yaml(tear_sheet, f"{out_dir}/tear_sheet.yaml")

    # Save Trades CSV

    trades = metrics.get("trades", [])
    if trades:
        # Convert objects to dicts if needed
        trades_data = [t.__dict__ if hasattr(t, "__dict__") else t for t in trades]
        pd.DataFrame(trades_data).to_csv(f"{out_dir}/trades.csv", index=False)
        print(f"  [x] Saved {len(trades)} trades to trades.csv")

    # Save Equity CSV
    # Re-run simulation raw? Or extract from gate details if stored?
    # Gates run engine.run_backtest.
    # Currently evaluate_gates does NOT return the equity curve in details to save memory?
    # Let's check engine.py or gates.py.
    # In gates.py: details["equity_curve"] = ... is NOT standard.
    # So we must re-run raw sim to get equity curve for CSV.

    df = load_ohlc(args.symbol, start_date, args.end, dcfg)
    prepared = strat.prepare_data(df, final_params)
    backtest_res = run_backtest(df, prepared, final_params, EngineConfig(), debug=args.debug)
    equity = backtest_res.equity_curve

    equity.to_csv(f"{out_dir}/equity.csv")
    print("  [x] Saved equity curve to equity.csv")
    # Phase 10: Trace & Metadata
    if not backtest_res.trace.empty:
        safe_to_csv(backtest_res.trace, f"{out_dir}/router_trace.csv", index=False)

    # Forensic Debug Artifacts
    if args.debug:
        audit_path = Path(out_dir) / "FORENSIC_AUDIT.json"
        if audit_path.exists():
            print(f"  🔬 Forensic Audit saved to {audit_path}")
        else:
            print("  ⚠️  Debug mode active but no Forensic Audit was emitted (no invariant events).")

    save_run_metadata(
        out_dir,
        config={"strategy": args.strategy, "params": final_params.model_dump()},
        cmd_args=vars(args),
        extra={
            "periods_per_year": infer_periods_per_year(args.interval, is_crypto=True)
        },  # Spotcheck defaults to crypto
    )

    print(f"\n✅ Spotcheck Complete. Results in {out_dir}")


def cmd_eval_fixed(args: argparse.Namespace) -> None:
    print(f"CROSS-ASSET CHECK: {args.symbols} @ {args.timeframes}")
    out_dir = args.output
    os.makedirs(out_dir, exist_ok=True)

    data = load_yaml(args.input)
    if isinstance(data, dict):
        configs = [data]
    elif isinstance(data, list):
        configs = data
    else:
        print("Error: Input YAML must be dict or list.")
        return

    symbols = [s.strip() for s in args.symbols.split(",")]
    timeframes = [t.strip() for t in args.timeframes.split(",")]

    results = []

    for cfg in configs:
        valid_keys = set(StrategyParams.__annotations__.keys())
        p_dict = {k: v for k, v in cfg.items() if k in valid_keys}
        params = StrategyParams(**p_dict)

        for s in symbols:
            for tf in timeframes:
                print(f"  Eval: {s} {tf} | {params}")
                data_cfg = DataConfig(interval=tf)

                r = _run_one(
                    strategy_name=args.strategy,
                    params=params,
                    data_cfg=data_cfg,
                    engine_cfg=EngineConfig(),
                    thresholds=GateThresholds(),
                    include_ablation=False,
                    include_time_split=False,
                    symbol=s,
                    start=args.start,
                    end=args.end,
                    gate_profile=args.gate_profile,
                    interval=tf,
                )

                flat = {
                    "source_config": cfg.get("note", "candidate"),
                    "symbol": s,
                    "timeframe": tf,
                    "status": r.status,
                    "profit_factor": r.metrics.profit_factor,
                    "profit_score": r.metrics.profit_score,
                    "calmar_ratio": r.metrics.calmar_ratio,
                    "max_dd_pct": r.metrics.max_dd_pct,
                    "trade_count": r.metrics.trade_count,
                    "fail_reason": r.fail_reason,
                }
                flat.update(p_dict)
                results.append(flat)

    df = pd.DataFrame(results)
    if not df.empty:
        safe_to_csv(df, f"{out_dir}/cross_asset_matrix_long.csv", index=False)

        try:
            # Multi-value pivot
            pivot = df.pivot(
                index="source_config", columns="symbol", values=["status", "profit_factor", "trade_count", "max_dd_pct"]
            )
            # Flatten columns: Symbol_Metric
            pivot.columns = [f"{c[1]}_{c[0]}" for c in pivot.columns]
            pivot = pivot.reset_index()
            safe_to_csv(pivot, f"{out_dir}/cross_asset_matrix.csv", index=False)
            print(f"Saved matrices to {out_dir}")
        except Exception as e:
            print(f"Pivot failed (saving long only): {e}")
            safe_to_csv(df, f"{out_dir}/cross_asset_matrix.csv", index=False)
    else:
        print("No results.")


def cmd_snapshot(args: argparse.Namespace) -> None:
    print(f"🔒 SNAPSHOT: {args.symbol} {args.timeframe}")
    path, h8 = save_snapshot(args.symbol, args.start, args.end, args.timeframe)
    print(f"  [x] Saved immutable: {path}")
    print(f"  [x] Hash: {h8}")


def cmd_walk_forward(args: argparse.Namespace) -> None:
    print(f"🚶 WALK-FORWARD: {args.symbol} {args.timeframe} (Profile: {args.gate_profile})")

    # 1. Ensure Snapshot
    # If explicit path not provided, try to find or create?
    # For now, require snapshot path or create ad-hoc?
    # Let's create ad-hoc for CLI usability
    path = args.snapshot
    if not path:
        print("  Auto-snapshotting for WF...")
        path, _ = save_snapshot(args.symbol, args.start, args.end, args.timeframe)

    # 2. Parse Params
    # Needs to accept params like spotcheck? or yaml?
    # For simplicity, load from config file
    if args.config:
        cfg = load_yaml(args.config)
        # Filter valid keys
        valid_keys = set(StrategyParams.__annotations__.keys())
        p_dict = {k: v for k, v in cfg.items() if k in valid_keys}
        params = StrategyParams(**p_dict)
    else:
        # Defaults
        params = StrategyParams()
        print(" Using DEFAULT Strategy Params (pass --config to override)")

    # 3. Run WF
    res = walk_forward_validation(
        args.symbol,
        args.timeframe,
        path,
        args.gate_profile,
        args.strategy,
        params,
        train_days=365,
        test_days=args.test_days,
        step_days=args.step_days,
        registry=STRATEGY_REGISTRY,
    )

    # 4. Report
    print(f"\n✅ RESULT: {res['status']}")
    print(f"  Reason: {res['reason']}")
    print(f"  Pass Ratio: {res.get('pass_ratio', 0):.1%}")
    if args.verbose:
        for split in res.get("splits", []):
            print(
                f"   - {split['test_start']}..{split['test_end']}: P={split['profit_status']} S={split['safety_status']} (PF={split['pf']:.2f})"  # noqa: E501
            )


def cmd_stage_candidate(args: argparse.Namespace) -> None:
    # HYDRA GUARD: Input Sanitization (Vector 36)
    args.symbol = _sanitize_string(args.symbol)
    args.strategy = _sanitize_string(args.strategy)
    args.gate_profile = _sanitize_string(args.gate_profile)
    
    print("🏆 STAGE CANDIDATE (Phase 6F Minimal)")

    # Check for legacy alias usage
    if getattr(args, "cmd", "") == "update-champion":
        print("⚠️ WARNING: 'update-champion' is deprecated. Use 'stage-candidate'.")

    # 1. Snapshot
    print(f"1. Snapshotting {args.symbol}...")
    snap_path, snap_hash = save_snapshot(args.symbol, args.start, args.end, args.timeframe)
    print(f"   Hash: {snap_hash}")

    # 2. Walk-Forward (Validate Candidate)
    # Load params
    if args.config:
        cfg = load_yaml(args.config)
        valid_keys = set(StrategyParams.__annotations__.keys())
        p_dict = {k: v for k, v in cfg.items() if k in valid_keys}
        params = StrategyParams(**p_dict)
    else:
        params = StrategyParams()  # Defaults

    print("2. Validating Candidate (Walk-Forward)...")
    res = walk_forward_validation(
        args.symbol,
        args.timeframe,
        snap_path,
        args.gate_profile,
        args.strategy,
        params,
        train_days=365,
        test_days=args.test_days,
        step_days=args.step_days,
        registry=STRATEGY_REGISTRY,
    )

    if res["status"] != "PASS":
        print(f"❌ Candidate Failed Validation: {res['status']} ({res['reason']})")
        sys.exit(1)

    print(f"✅ Validation Passed. Pass Ratio: {res.get('pass_ratio', 0):.1%}")

    # 3. Registry Update (STAGING)
    # Load snapshot DF for metrics calculation
    print(f"3. Calculating Lifetime Metrics (Strategy: {args.strategy})...")
    print(f"   Source: Snapshot {snap_hash[:8]} ({snap_path})")
    print(f"   Config: {args.config if args.config else 'DEFAULT'}")

    # GOVERNANCE CHECK (Staging requires at least Lab?)
    STRATEGY_REGISTRY.verify_strategy_allowed(args.strategy, mode="research")

    df_snap = load_snapshot(snap_path)

    sim_res = _run_one(
        args.strategy,
        params,
        DataConfig(interval=args.timeframe),
        EngineConfig(),
        GateThresholds(),
        False,
        False,
        args.symbol,
        args.start,
        args.end,
        args.gate_profile,
        args.timeframe,
        snapshot_df=df_snap,
        registry=STRATEGY_REGISTRY,
    )

    candidate_metrics = {
        "profit_factor": sim_res.metrics.profit_factor,
        "max_dd_pct": sim_res.metrics.max_dd_pct,
        "sharpe_ratio": sim_res.metrics.sharpe_ratio,
        "trade_count": sim_res.metrics.trade_count,
        "snapshot_hash": snap_hash,
        "wf_pass_ratio": res.get("pass_ratio", 0.0),
    }

    print("3. Promoting to STAGING...")
    # Anchor? Optional. If we have a previous registry entry, promote compares.
    # We pass reset_anchor if user requested.
    reg_res = promote_to_staging(
        args.symbol, args.timeframe, candidate_metrics, reset_anchor=getattr(args, "reset_anchor", False)
    )

    if reg_res["status"] == "FAIL":
        print(f"❌ Promotion Failed: {reg_res['reason']}")
        sys.exit(1)

    print(f"🏆 SUCCESS: Promoted to STAGING. {reg_res['message']}")
    sys.exit(0)



def build_parser() -> argparse.ArgumentParser:  # noqa: PLR0915
    p = argparse.ArgumentParser(prog="antigravity_harness", description="FORTRESS PROTOCOL harness")
    p.add_argument("--debug", "-d", action="store_true", help="Enable high-fidelity forensic telemetry")
    sub = p.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("calibrate", help="Run grid search + plateau selection")
    c.add_argument("--grid", required=True, help="Path to grid YAML")
    c.add_argument("--strategy", default="v032_simple")
    c.add_argument("--output-dir", default=str(REPORT_DIR / "artifacts"))
    c.add_argument("--jobs", type=int, default=-1, help="joblib n_jobs (-1=all cores)")
    c.add_argument("--include-ablation", action="store_true", help="Run Gate2 ablation on every grid point (slower)")
    c.add_argument(
        "--include-time-split", action="store_true", help="Run Gate5 time-split on every grid point (very slow)"
    )
    c.add_argument("--symbol", default="SPY")
    c.add_argument("--symbols", default=None, help="Comma-separated symbols (e.g. BTC-USD,ETH-USD)")
    c.add_argument("--start", default="2000-01-01")
    c.add_argument("--end", default="2024-12-31")
    c.add_argument("--interval", default="1d")
    c.add_argument(
        "--gate-profile", default="equity_fortress", help="Validation profile: equity_fortress | crypto_profit"
    )
    c.add_argument("--timeframes", default=None, help="Comma-separated timeframes (overrides grid)")
    c.add_argument("--equity", action="store_true", help="Use Equity (252 days) physics")
    c.set_defaults(func=cmd_calibrate)

    v = sub.add_parser("validate", help="Run full gate validation on one config")
    v.add_argument("--strategy", default="v032_simple")
    v.add_argument("--output-dir", default=str(REPORT_DIR / "artifacts"))
    v.add_argument("--config", help="YAML with params (ma_length, rsi_entry, rsi_exit, stop_atr)")
    v.add_argument("--ma-length", type=int, default=200)
    v.add_argument("--rsi-entry", type=int, default=30)
    v.add_argument("--rsi-exit", type=int, default=70)
    v.add_argument("--stop-atr", type=float, default=2.0)
    v.add_argument("--no-ablation", action="store_true")
    v.add_argument("--time-split", action="store_true")
    v.add_argument(
        "--gate-profile", default="equity_fortress", help="Validation profile: equity_fortress | crypto_profit"
    )
    # Added Args
    v.add_argument("--symbol", default="SPY")
    v.add_argument("--start", default="2000-01-01")
    v.add_argument("--end", default="2024-12-31")
    v.add_argument("--interval", default="1d")
    v.add_argument("--equity", action="store_true", help="Use Equity (252 days) physics")
    v.set_defaults(func=cmd_validate)

    ef = sub.add_parser("eval_fixed", help="Run fixed configs on multiple assets")
    ef.add_argument("--strategy", required=True)
    ef.add_argument("--input", required=True, help="Path to yaml with list of configs (or single config)")
    ef.add_argument("--symbols", required=True)
    ef.add_argument("--timeframes", required=True)
    ef.add_argument("--gate-profile", default="equity_fortress")
    ef.add_argument("--output", required=True)
    ef.add_argument("--start", default="2020-01-01")
    ef.add_argument("--end", default="2025-01-01")
    ef.set_defaults(func=cmd_eval_fixed)

    i = sub.add_parser("info", help="Display project health and registry status")
    i.set_defaults(func=cmd_info)

    e = sub.add_parser("emit-signals", help="Generate production signals (JSON view)")
    e.add_argument("--strategy", required=True)
    e.add_argument("--symbol", required=True)
    e.add_argument("--timeframe", default="1d")
    e.add_argument("--lookback", type=int, default=400)
    e.add_argument(
        "--end-date", default="2030-01-01", help="Load data up to this date (defaults to future to capture 'now')"
    )
    e.add_argument("--config", help="Path to param yaml (fortress_candidate.yaml)")
    e.add_argument("--output", help="Path to output JSON file (optional)")
    e.set_defaults(func=cmd_emit)

    s = sub.add_parser("spotcheck", help="Run detailed single simulation with explicit params")
    s.add_argument("--strategy", required=True)
    s.add_argument("--symbol", required=True)
    s.add_argument("--interval", default="1d")
    s.add_argument("--params", required=True, help="Key=Value string, e.g. 'ma_length=150,rsi_entry=65'")
    s.add_argument("--start", default="2020-01-01")
    s.add_argument("--end", default="2025-01-01")
    s.add_argument("--output-dir", help="Directory to save tear sheet and csvs")
    s.add_argument("--gate-profile", default="equity_fortress")
    s.set_defaults(func=cmd_spotcheck)

    # Phase 6F Commands
    snap = sub.add_parser("snapshot-data", help="Create immutable data snapshot")
    snap.add_argument("--symbol", required=True)
    snap.add_argument("--timeframe", default="1d")
    snap.add_argument("--start", default="2016-01-01")
    snap.add_argument("--end", default="2025-01-01")
    snap.set_defaults(func=cmd_snapshot)

    wf = sub.add_parser("walk-forward", help="Run walk-forward validation on a snapshot")
    wf.add_argument("--symbol", required=True)
    wf.add_argument("--timeframe", default="1d")
    wf.add_argument("--strategy", default="v032_simple")
    wf.add_argument("--config", help="Param YAML")
    wf.add_argument("--gate-profile", default="equity_fortress")
    wf.add_argument("--test-days", type=int, default=90)
    wf.add_argument("--step-days", type=int, default=30)
    wf.add_argument(
        "--snapshot", help="Path to existing snapshot (optional, else specific symbol/start/end is snapshotted)"
    )
    wf.add_argument("--start", default="2016-01-01")
    wf.add_argument("--end", default="2025-01-01")
    wf.add_argument("--verbose", action="store_true")
    wf.set_defaults(func=cmd_walk_forward)

    # Stage Candidate (Honest Command Name)
    sc = sub.add_parser("stage-candidate", help="Automated Staging Promotion")
    add_stage_candidate_args(sc)
    sc.set_defaults(func=cmd_stage_candidate)

    # Legacy Alias
    uc = sub.add_parser("update-champion", help="[DEPRECATED] Use stage-candidate")
    add_stage_candidate_args(uc)
    uc.set_defaults(func=cmd_stage_candidate)

    # Certification Run (Task E)
    cr = sub.add_parser("certify-run", help="Full Certification Bundle (Snapshot+WF+Calib+Manifest)")
    cr.add_argument("--symbols", required=True)
    cr.add_argument("--timeframes", required=True)
    cr.add_argument("--gate-profile", required=True)
    cr.add_argument("--lookback-days", type=int, default=730)
    cr.add_argument("--train-days", type=int, default=365)
    cr.add_argument("--test-days", type=int, default=90)
    cr.add_argument("--step-days", type=int, default=30)
    cr.add_argument("--outdir", default="auto")
    # Added Args for Task 4
    cr.add_argument("--strategy", default="v040_alpha_prime", help="Default: Tier 2 Candidate (Safe)")
    cr.add_argument("--config", help="Strategy params YAML")
    cr.add_argument("--end", default=None, help="End date YYYY-MM-DD")
    cr.add_argument("--allow-quarantined", action="store_true", help="Allow running quarantined strategies (e.g. v032)")
    cr.set_defaults(func=run_certification_proxy)

    # Certification Sweep (Task 2.1)
    cs = sub.add_parser("certify-sweep", help="Strategy Discovery Sweep")
    cs.add_argument("--symbols", required=True)
    cs.add_argument("--timeframes", required=True)
    cs.add_argument("--strategy", default="v040_alpha_prime", help="Default: Tier 2 Candidate (Safe)")
    cs.add_argument("--gate-profile", required=True)
    cs.add_argument("--config-grid", help="Path to grid YAML (optional, defaults to single run)")
    cs.add_argument("--outdir", required=True)
    cs.add_argument("--lookback-days", type=int, default=730)
    cs.add_argument("--train-days", type=int, default=365)
    cs.add_argument("--test-days", type=int, default=90)
    cs.add_argument("--step-days", type=int, default=30)
    cs.add_argument("--end", default=None)
    cs.add_argument("--allow-quarantined", action="store_true", help="Allow running quarantined strategies (e.g. v032)")
    # Lazy import to avoid circular dependency at top level?
    # No, top level import is fine if structure is cleaner.
    # But cli imports everything.
    cs.set_defaults(func=run_sweep_proxy)

    # Cert Bundle Verifier (Task 2.2)
    cb = sub.add_parser("verify-cert-bundle", help="Reviewer-grade bundle integrity check")
    cb.add_argument("--manifest", required=True, help="Path to MANIFEST.json")
    cb.set_defaults(func=run_verify_proxy)

    # Strategy Catalog (Task 3.2)
    ls = sub.add_parser("list-strategies", help="Show Strategy Catalog (Tiers/Quarantine)")
    ls.set_defaults(func=cmd_list_strategies)

    # Reality Gap Sensor (Phase 8 Task B)
    rg = sub.add_parser("reality-gap", help="Measure reality gap (execution drag)")
    rg.add_argument("--fills", required=True, help="Path to fills.csv")
    rg.add_argument("--signals", required=True, help="Path to signals.csv")
    rg.add_argument("--outdir", required=True)
    rg.set_defaults(func=cmd_reality_gap)

    # Council Sweep (Task 6)
    cs = sub.add_parser("council-sweep", help="Institutional Council Sweep Protocol")
    cs.add_argument("--symbols", default="BTC-USD,ETH-USD,SOL-USD", help="Symbols to sweep")
    cs.add_argument("--timeframes", default="4h,6h,8h,12h,1d", help="Timeframes to sweep")
    cs.add_argument("--allow-quarantined", action="store_true", help="Include quarantined strategies")
    cs.add_argument("--outdir", help="Output directory")
    cs.set_defaults(func=cmd_council_sweep)

    # Portfolio Backtest (Phase 9A + 9D Safety Overlay)
    pb = sub.add_parser("portfolio-backtest", help="Run multi-asset portfolio with regime router")
    pb.add_argument("--symbols", required=True, help="Comma-separated symbols")
    pb.add_argument("--start", default="2020-01-01")
    pb.add_argument("--end", default="2024-12-31")
    pb.add_argument("--interval", default="1d")
    pb.add_argument("--rebalance", default="M", help="Rebalance frequency (W, M, Q)")
    pb.add_argument("--router", default="regime_v1", help="Router preset: regime_v1 | none")
    pb.add_argument("--outdir", required=True)
    pb.add_argument("--strategy-base", default="v032_simple", help="Base strategy for data prep")
    # Phase 9D: Safety Overlay flags
    pb.add_argument("--dd_reduce", type=float, default=-0.15, help="DD threshold for RISK_REDUCE")
    pb.add_argument("--dd_off", type=float, default=-0.25, help="DD threshold for RISK_OFF")
    pb.add_argument("--dd_hard", type=float, default=-0.40, help="DD threshold for HARD_FAIL_TRIGGER")
    pb.add_argument("--reduce_multiplier", type=float, default=0.5, help="Weight scale in RISK_REDUCE")
    pb.add_argument("--reentry_off", type=float, default=-0.20, help="DD recovery to exit RISK_OFF")
    pb.add_argument("--reentry_reduce", type=float, default=-0.10, help="DD recovery to exit RISK_REDUCE")
    pb.add_argument("--max_weight_per_asset", type=float, default=0.50, help="Max weight per asset")
    pb.add_argument("--min_positions", type=int, default=1, help="Min distinct positions")
    pb.add_argument("--enable_shock_overlay", action="store_true", help="Enable shock trigger")
    pb.add_argument("--shock_ret_thresh", type=float, default=-0.12, help="1-bar crash return threshold")
    pb.add_argument("--shock_vol_ratio", type=float, default=2.0, help="Vol spike ratio for shock")
    pb.add_argument("--fetch", action="store_true", help="Enable network download (default: OFF)")
    pb.add_argument("--prices-csv", type=str, default=None, help="Path to local close-matrix CSV (offline mode)")
    pb.add_argument("--synthetic", action="store_true", help="Use deterministic synthetic data for smoke testing")
    pb.add_argument("--equity", action="store_true", help="Use Equity (252 days) physics instead of Crypto (365)")
    pb.set_defaults(func=cmd_portfolio_backtest)

    # Help All (Institutional Discovery)
    ha = sub.add_parser("help-all", help="Display all project commands and scripts")
    ha.set_defaults(func=cmd_help_all)

    # Forensic Debug Playback
    dbg = sub.add_parser("debug-playback", help="Forensic playback of an AUDIT_REPORT.json")
    dbg.add_argument("--report", required=True, help="Path to AUDIT_REPORT.json")
    dbg.add_argument("--filter", default=None, help="Filter decisions by type (e.g. ENTRY_EXEC, EXIT_REJECTED)")
    dbg.add_argument("--summary", action="store_true", help="Show summary statistics only")
    dbg.add_argument("--bar-range", default=None, help="Bar index range to display (e.g. 100-200)")
    dbg.set_defaults(func=cmd_debug_playback)

    return p

def cmd_debug_playback(args: argparse.Namespace) -> None:  # noqa: PLR0915
    """
    Forensic Debug Playback: Read a saved AUDIT_REPORT.json and present
    a human-readable bar-by-bar walkthrough of every trading decision.
    """
    report_path = Path(args.report)
    if not report_path.exists():
        print(f"❌ Report not found: {report_path}")
        return

    with open(report_path, encoding="utf-8") as f:
        report = json.load(f)

    decisions = report.get("forensic_decisions", [])
    events = report.get("events", [])
    final_state = report.get("final_state", {})
    invariants_passed = report.get("invariants_passed", True)
    session_id = report.get("audit_session_id", "unknown")
    duration = report.get("duration_sec", 0)

    print("🔬 FORENSIC DEBUG PLAYBACK")
    print("=" * 60)
    print(f"  Session:    {session_id}")
    print(f"  Duration:   {duration:.2f}s")
    print(f"  Invariants: {'✅ PASSED' if invariants_passed else '❌ VIOLATED'}")
    print(f"  Final Cash: ${final_state.get('cash', 0):,.2f}")
    print(f"  Final Qty:  {final_state.get('qty', 0):.6f}")
    print(f"  Events:     {len(events)}")
    print(f"  Decisions:  {len(decisions)}")
    print("=" * 60)

    if not decisions:
        print("\n⚠️  No forensic decisions captured. Was --debug enabled during the simulation?")
        if events:
            print(f"\n📋 {len(events)} audit events are present:")
            for ev in events:
                print(f"  [{ev.get('event', '?')}] {ev.get('data', {})}")
        return

    # Parse optional filters
    bar_start, bar_end = 0, float("inf")
    if args.bar_range:
        parts = args.bar_range.split("-")
        bar_start = int(parts[0])
        bar_end = int(parts[1]) if len(parts) > 1 else bar_start

    decision_filter = args.filter.upper() if args.filter else None

    # Summary mode
    if args.summary:
        _print_debug_summary(decisions)
        return

    # Full playback
    print(f"\n{'BAR':>6} | {'TIMESTAMP':>22} | {'DECISION':<18} | CONTEXT")
    print("-" * 90)

    displayed = 0
    for d in decisions:
        idx = d.get("bar_idx", -1)
        if idx < bar_start or idx > bar_end:
            continue
        if decision_filter and d.get("decision", "") != decision_filter:
            continue

        ts = d.get("timestamp", "")[:22]
        dec = d.get("decision", "?")
        ctx = d.get("context", {})

        # Color-code decision types
        icon = _decision_icon(dec)
        ctx_str = _format_context(ctx)
        print(f"{idx:>6} | {ts:>22} | {icon} {dec:<15} | {ctx_str}")
        displayed += 1

    print("-" * 90)
    print(f"Displayed {displayed}/{len(decisions)} decisions.")

    # Always print summary at the end
    print()
    _print_debug_summary(decisions)


def _decision_icon(decision: str) -> str:
    """Map decision types to visual icons."""
    icons = {
        "ENTRY_EXEC": "🟢",
        "ENTRY_SKIPPED": "🟡",
        "ENTRY_REJECTED": "🔴",
        "FULL_EXIT": "🔵",
        "PARTIAL_EXIT": "🟣",
        "EXIT_SKIPPED": "🟡",
        "EXIT_REJECTED": "🔴",
        "STOP_LOSS": "🛑",
        "FORCE_CLOSE": "⏹️",
    }
    return icons.get(decision, "⚪")


def _format_context(ctx: dict) -> str:
    """Format a context dict into a concise one-line string."""
    parts = []
    for k, v in ctx.items():
        if isinstance(v, float):
            if k == "price":
                parts.append(f"{k}=${v:,.2f}")
            elif k == "risk":
                parts.append(f"{k}={v:.1%}")
            else:
                parts.append(f"{k}={v:.4f}")
        else:
            parts.append(f"{k}={v}")
    return ", ".join(parts)


def _print_debug_summary(decisions: list) -> None:
    """Print aggregate statistics from forensic decisions."""
    from collections import Counter  # noqa: PLC0415
    counts = Counter(d.get("decision", "?") for d in decisions)

    print("📊 DECISION SUMMARY")
    print("-" * 40)
    for dec_type in ["ENTRY_EXEC", "ENTRY_SKIPPED", "ENTRY_REJECTED",
                     "FULL_EXIT", "PARTIAL_EXIT", "EXIT_SKIPPED", "EXIT_REJECTED",
                     "STOP_LOSS", "FORCE_CLOSE"]:
        c = counts.get(dec_type, 0)
        if c > 0:
            icon = _decision_icon(dec_type)
            print(f"  {icon} {dec_type:<18} {c:>5}")

    # Unknown types
    known = {"ENTRY_EXEC", "ENTRY_SKIPPED", "ENTRY_REJECTED",
             "FULL_EXIT", "PARTIAL_EXIT", "EXIT_SKIPPED", "EXIT_REJECTED",
             "STOP_LOSS", "FORCE_CLOSE"}
    for dec_type, c in counts.items():
        if dec_type not in known:
            print(f"  ⚪ {dec_type:<18} {c:>5}")

    total = len(decisions)
    entries = counts.get("ENTRY_EXEC", 0)
    exits = counts.get("FULL_EXIT", 0) + counts.get("PARTIAL_EXIT", 0) + counts.get("STOP_LOSS", 0) + counts.get("FORCE_CLOSE", 0)
    rejected = counts.get("ENTRY_REJECTED", 0) + counts.get("EXIT_REJECTED", 0)
    skipped = counts.get("ENTRY_SKIPPED", 0) + counts.get("EXIT_SKIPPED", 0)

    print(f"\n  Total Decisions:  {total}")
    print(f"  Executed:         {entries + exits} ({(entries + exits) / max(1, total) * 100:.1f}%)")
    print(f"  Rejected:         {rejected} ({rejected / max(1, total) * 100:.1f}%)")
    print(f"  Skipped:          {skipped} ({skipped / max(1, total) * 100:.1f}%)")
    print("-" * 40)


def cmd_help_all(args: argparse.Namespace) -> None:
    """Display comprehensive help for the entire project landscape."""
    print("🦅 ANTIGRAVITY HARNESS: THE COMPLETE COMMAND INDEX")
    print("-" * 60)
    print("\n[MAIN CLI COMMANDS]")
    print("  calibrate         - Parameter grid search and plateau discovery")
    print("  validate          - Full 6-gate validation on a single config")
    print("  certify-run       - Full certification bundle creation")
    print("  portfolio-backtest - Multi-asset simulation with safety overlays")
    print("  stage-candidate   - Promote a validated config to STAGING")
    print("  council-sweep     - Run discovery sweep across all targets")
    print("  info              - Display project sanity and health status")
    print("  list-strategies   - List all strategies (Tiers/Quarantine)")
    print("  reality-gap      - Execution drag forensic analysis")
    print("  debug-playback    - Forensic playback of AUDIT_REPORT.json (--debug)")
    print("  spotcheck         - Rapid tear-sheet generation for one config")
    print("  snapshot-data     - Create immutable data witnesses")
    print("  verify-cert-bundle - Third-party audit of certification artifacts")
    
    print("\n[CORE SCRIPTS (scripts/)]")
    scripts = {
        "one_true_command.sh": "The Sovereign Audit (strict, fail-closed verification)",
        "make_drop_packet.py": "Bundles v4.5.x graduate artifacts into a signed drop",
        "clean_repo.py": "Enforces repository purity (removes pycache/logs)",
        "preflight.py": "Runs the full institutional pre-graduation suite",
        "chaos_sweep.py": "Automated recursive stress test of all Hydra vectors",
        "chaos_hydra_monkey.py": "Unified saboteur for targeted security testing",
        "verify_drop_packet.py": "Deep surgical audit of build artifacts",
        "vault_keeper.py": "Cryptographic sealing and signing utility",
        "check_dependency_cycles.py": "Ensures architectural modularity",
    }
    for s, desc in scripts.items():
        print(f"  {s:<22} - {desc}")
    
    print("\n[MAKEFILE TARGETS]")
    print("  make all          - Full preflight + Graduation + Verification")
    print("  make build        - Create a graduate drop packet (dist/)")
    print("  make verify       - Run the Sovereign Audit on latest dist")
    print("  make clean        - Reset to a pure repository state")
    print("-" * 60)
    print("Run any CLI command with -h for details. Example: 'python3 -m antigravity_harness.cli calibrate -h'")

def cmd_reality_gap(args: argparse.Namespace) -> None:

    run_reality_gap(args.fills, args.signals, args.outdir)


def cmd_council_sweep(args: argparse.Namespace) -> None:
    """Institutional Council Sweep Protocol."""

    run_council_sweep(args.symbols, args.timeframes, args.allow_quarantined, args.outdir)


def _enforce_quarantine(args: argparse.Namespace) -> None:

    strat_name = args.strategy
    if strat_name not in STRATEGY_CATALOG:
        # Unknown strategy, might fail later, but check here if possible
        return

    entry = STRATEGY_CATALOG[strat_name]
    if entry.is_quarantined and not getattr(args, "allow_quarantined", False):
        print(f"❌ QUARANTINED_STRATEGY_REFUSED: '{strat_name}' is quarantined coverage-only.")
        print("   Pass --allow-quarantined to override (defaults to fail for discovery/baselines).")
        sys.exit(1)


def cmd_list_strategies(args: argparse.Namespace) -> None:

    print(f"{'NAME':<30} | {'TIER':<5} | {'REGIME':<10} | {'DESCRIPTION'}")
    print("-" * 100)

    # Sort: Tier 1, then Tier 2, then Baseline (0)
    order = sorted(STRATEGY_CATALOG.values(), key=lambda x: (x.is_quarantined, -x.tier, x.name))

    for s in order:
        tier_str = str(s.tier) if not s.is_quarantined else "BASE"
        status = "⛔" if s.is_quarantined else "✅"
        print(f"{status} {s.name:<27} | {tier_str:<5} | {s.regime:<10} | {s.description}")


def cmd_portfolio_backtest(args: argparse.Namespace) -> None:  # noqa: PLR0912, PLR0915
    print(f"PORTFOLIO BACKTEST: {args.symbols} (Router: {args.router})")
    out_dir = Path(args.outdir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Load Data

    if args.synthetic:
        # Generate Synthetic Data (Deterministic)
        print("  Generating Synthetic Data...")
        np.random.seed(42)
        dates = pd.date_range("2021-01-01", periods=200, freq="D")
        symbols = ["MOCK1", "MOCK2", "MOCK3"]
        data_map = {}
        for sym in symbols:
            # Random walk
            returns = np.random.normal(0.0005, 0.02, size=len(dates))
            prices = 100 * (1 + returns).cumprod()
            df = pd.DataFrame(
                {
                    "Open": prices,
                    "High": prices * 1.01,
                    "Low": prices * 0.99,
                    "Close": prices,
                    "Volume": 10000,
                },
                index=dates,
            )
            data_map[sym] = df
    else:
        symbols = [s.strip() for s in args.symbols.split(",")]
        dcfg = DataConfig(interval=args.interval)
        data_map = {}

        if args.prices_csv:
            # Offline: load from CSV
            print(f"  Loading data from CSV: {args.prices_csv}")
            p = Path(args.prices_csv)
            
            # Phase 10: MarketTape Support
            # If it's a single symbol and looks like a tape (contains timestamp_utc), use MarketTape loader
            try:
                # Peak at header
                with open(p, "r") as f:
                    header = f.readline().lower()
                
                if "timestamp_utc" in header and len(symbols) == 1:
                    print(f"  ⚡ Tape Mode: Loading {symbols[0]} via MarketTape")
                    tape = MarketTape.from_csv(p)
                    data_map[symbols[0]] = tape.df
                else:
                    # Legacy matrix loader
                    close_df = pd.read_csv(p, index_col=0, parse_dates=True)
                    
                    # Phase 10: OHLCV Fallback
                    if len(symbols) == 1 and all(c in close_df.columns for c in ["Open", "High", "Low", "Close"]):
                        print(f"  ⚡ OHLCV Mode: Loading {symbols[0]} via OHLCV matrix")
                        data_map[symbols[0]] = close_df
                    else:
                        for sym in symbols:
                            if sym not in close_df.columns:
                                print(f"  [!] Symbol {sym} not found in CSV columns: {list(close_df.columns)}")
                                continue
                            prices = close_df[sym].dropna()
                            df = pd.DataFrame(
                                {
                                    "Open": prices,
                                    "High": prices * 1.005,
                                    "Low": prices * 0.995,
                                    "Close": prices,
                                    "Volume": 10000,
                                },
                                index=prices.index,
                            )
                            data_map[sym] = df
            except Exception as e:
                print(f"  [!] Failed to load CSV {p}: {e}")
                return
        elif args.fetch:
            print("  Loading data... (Network: ON)")
            for sym in symbols:
                try:
                    df = load_ohlc(sym, args.start, args.end, dcfg, use_network=True)
                    data_map[sym] = df
                except Exception as e:
                    print(f"  [!] Failed to load {sym}: {e}")
        else:
            print("❌ No data source specified. Use --prices-csv <path> or --fetch or --synthetic.")
            return

    if not data_map:
        print("❌ No data loaded.")
        return

    # 2. Config Router + Safety (Phase 9D)
    regime_cfg = RegimeConfig()

    # Phase 10.3: Unified Physics
    is_crypto = not args.equity
    inferred_periods = infer_periods_per_year(args.interval, is_crypto=is_crypto)

    policy_cfg = PolicyConfig(
        max_weight_per_asset=args.max_weight_per_asset,
        min_positions=args.min_positions,
        is_crypto=is_crypto,
        periods_per_year=inferred_periods,
    )
    safety_cfg = SafetyConfig(
        dd_reduce=args.dd_reduce,
        dd_off=args.dd_off,
        dd_hard=args.dd_hard,
        reduce_multiplier=args.reduce_multiplier,
        reentry_off=args.reentry_off,
        reentry_reduce=args.reentry_reduce,
        enable_shock=args.enable_shock_overlay,
        shock_ret_thresh=args.shock_ret_thresh,
        shock_vol_ratio=args.shock_vol_ratio,
    )

    router = None
    if args.router == "regime_v1":
        router = PortfolioRouter(regime_cfg, policy_cfg, interval=args.interval)
    elif args.router == "none":
        router = None
    else:
        print(f"⚠️ Unknown router '{args.router}'. Using None (Static Rebal).")

    # 3. Run
    print("  Running Simulation...")
    strategy_cls = get_strategy(args.strategy_base).__class__

    portfolio, regime_log, curve = run_portfolio_backtest_verbose(
        data_map=data_map,
        strategy_cls=strategy_cls,
        strat_params=StrategyParams(),
        engine_config=EngineConfig(),
        rebalance_freq=args.rebalance,
        optimization_method="equal_weight" if not router else "",
        initial_cash=100_000.0,
        router=router,
        safety_cfg=safety_cfg,
        policy_cfg=policy_cfg,
        out_dir=Path(out_dir),
    )

    # 4. Save Artifacts
    print("  Saving Results...")
    # Equity Curve
    curve.to_csv(out_dir / "equity_curve.csv")

    # Trades? Portfolio trades are internal to PortfolioAccount?
    # PortfolioAccount tracks `trades`.
    # Let's verify `portfolio.trades` exists in `antigravity_harness/portfolio.py`.
    # Assuming it follows standard pattern.
    if hasattr(portfolio, "trades"):
        pd.DataFrame(portfolio.trades).to_csv(out_dir / "trades.csv", index=False)

    # Regime Report (with benchmark)
    close_prices_df = pd.DataFrame({s: df["Close"] for s, df in data_map.items()})

    metadata_config = {
        "cmd_args": {k: str(v) for k, v in vars(args).items() if k != "func"},
        "strategy_base": args.strategy_base,
        "router": args.router,
        "policy": policy_cfg.model_dump(),
        "safety": safety_cfg.model_dump(),
    }

    generate_regime_report(
        regime_log,
        curve,
        out_dir,
        periods_per_year=policy_cfg.periods_per_year,
        close_prices_df=close_prices_df,
        metadata_config=metadata_config,
    )

    # Council Brief
    _write_council_brief(regime_log, curve, out_dir, args)

    # Phase 4: Evidence Realism - Save Metadata
    save_run_metadata(
        str(out_dir),
        config={
            "strategy_base": args.strategy_base,
            "router": args.router,
            "rebalance": args.rebalance,
            "policy": policy_cfg.model_dump(),
            "safety": safety_cfg.model_dump(),
        },
        cmd_args={k: str(v) for k, v in vars(args).items() if k != "func"},
        extra={"periods_per_year": inferred_periods},
    )

    # Phase 4.1: Tier-0 results.csv (one-row, machine-friendly summary)
    _emit_results_csv(out_dir)

    # Phase 4.2: Evidence Manifest (Tier 1 Credibility)
    _generate_evidence_manifest(out_dir, args)

    # Final Stats
    final_eq = curve["equity"].iloc[-1]
    ret = (final_eq / 100_000.0) - 1.0
    print("✅ Backtest Complete.")
    print(f"   Final Equity: ${final_eq:,.2f}")
    print(f"   Total Return: {ret:.2%}")
    print(f"   Regime Log: {len(regime_log)} periods")
    print(f"   Artifacts: {out_dir}")


def _emit_results_csv(out_dir: Path) -> None:
    """Tier-0 results.csv (one-row, machine-friendly summary)."""
    try:
        summary_path = out_dir / "PORTFOLIO_SUMMARY.json"
        if summary_path.exists():
            with open(summary_path) as f:
                summary = json.load(f)
            overall = summary.get("overall", {})
            row = {
                "status": "SMOKE_OK",
                "fail_gate": "",
                "fail_reason": "",
                "profit_factor": overall.get("profit_factor"),
                "trade_count": overall.get("rebalance_events", 0),
                "sharpe_ratio": overall.get("sharpe_ratio"),
                "max_dd_pct": overall.get("overall_max_drawdown_pct"),
                "total_return_pct": overall.get("total_return_pct"),
            }
            pd.DataFrame([row]).to_csv(out_dir / "results.csv", index=False)
    except Exception as e:
        print(f"⚠️  Could not write results.csv: {e}")


def _write_council_brief(regime_log, curve, out_dir, args):
    """Write COUNCIL_PORTFOLIO_BRIEF.md to outdir and certification path."""

    # Load the summary we just wrote
    summary_path = out_dir / "PORTFOLIO_SUMMARY.json"
    if not summary_path.exists():
        return
    with open(summary_path) as f:
        summary = json.load(f)

    overall = summary.get("overall", {})
    per_regime = summary.get("per_regime", {})

    lines = [
        "# COUNCIL PORTFOLIO BRIEF",
        "",
        f"**Symbols**: {args.symbols}",
        f"**Period**: {args.start} → {args.end}",
        f"**Router**: {args.router}",
        f"**Rebalance**: {args.rebalance}",
        "",
        "## Overall",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Return | {overall.get('total_return_pct', 0):.2f}% |",
        f"| Sharpe | {overall.get('sharpe_ratio', 0):.2f} |",
        f"| Max DD | {overall.get('overall_max_drawdown_pct', 0):.2f}% |",
        f"| PF | {overall.get('profit_factor', 0):.2f} |",
        f"| Rebalances | {overall.get('rebalance_events', 0)} |",
        "",
        "## Per-Regime",
        "",
        "| Regime | Days | Return | Sharpe | DD (Global) | DD (Segment) |",
        "|--------|------|--------|--------|-------------|--------------|",
    ]
    for regime, s in per_regime.items():
        lines.append(
            f"| {regime} | {s['days_in_regime']} | {s['total_return_pct']:.2f}% | "
            f"{s['sharpe_ratio']:.2f} | {s.get('max_drawdown_pct_global', 0):.2f}% | {s.get('within_segment_max_drawdown_pct', 0):.2f}% |"  # noqa: E501
        )
    lines.append("")
    lines.append("---")
    lines.append(f"*Generated by antigravity_harness v{_ah.__version__}*")

    brief_text = "\n".join(lines)

    # Write to outdir
    with open(out_dir / "COUNCIL_PORTFOLIO_BRIEF.md", "w") as f:
        f.write(brief_text)

    # Write to certification path
    cert_dir = Path("reports/certification/PORTFOLIO")
    cert_dir.mkdir(parents=True, exist_ok=True)
    with open(cert_dir / "COUNCIL_PORTFOLIO_BRIEF.md", "w") as f:
        f.write(brief_text)


def _generate_evidence_manifest(out_dir: Path, args: argparse.Namespace) -> None:
    """
    Tier 1 Evidence Credibility:
    Generates a cryptographic manifest (EVIDENCE_MANIFEST.json) of all artifacts produced by the run.
    This binds the outputs to the active code state and environment.
    """
    print("🔐 Generating Evidence Manifest...")
    
    manifest = {
        "files": {},
        "environment": {
            "python_version": platform.python_version(),
            "platform": platform.platform(),
            "args": {k: str(v) for k, v in vars(args).items() if k != "func"}
        }
    }

    # Hash all files in output dir
    for path in sorted(out_dir.rglob("*")):
        if path.is_file() and path.name != "EVIDENCE_MANIFEST.json":
            rel_path = path.relative_to(out_dir).as_posix()
            
            # Streaming hash
            h = hashlib.sha256()
            with open(path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    h.update(chunk)
            
            manifest["files"][rel_path] = h.hexdigest()

    # Get Git Context if available
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL).decode("utf-8").strip()
        manifest["environment"]["git_commit"] = commit
    except Exception:
        manifest["environment"]["git_commit"] = "UNKNOWN"

    # Write Manifest
    with open(out_dir / "EVIDENCE_MANIFEST.json", "w") as f:
        json.dump(manifest, f, indent=2, sort_keys=True)
    
    print(f"   Manifest Secured: {out_dir / 'EVIDENCE_MANIFEST.json'}")

def run_verify_proxy(args: argparse.Namespace) -> None:

    cmd_verify(args)


def run_sweep_proxy(args: argparse.Namespace) -> None:
    _enforce_quarantine(args)
    run_sweep(args)


def run_certification_proxy(args: argparse.Namespace) -> None:
    _enforce_quarantine(args)
    run_certification(args)


def add_stage_candidate_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--symbol", required=True)
    p.add_argument("--timeframe", default="1d")
    p.add_argument("--strategy", default="v032_simple")
    p.add_argument("--config", help="Candidate Param YAML")
    p.add_argument("--gate-profile", default="equity_fortress")
    p.add_argument("--start", default="2016-01-01")
    p.add_argument("--end", default="2025-01-01")
    p.add_argument("--test-days", type=int, default=90)
    p.add_argument("--step-days", type=int, default=30)
    p.add_argument("--reset-anchor", action="store_true", help="Explicitly reset drift anchor metrics")


def main(argv: Any = None) -> None:
    # HYDRA GUARD: Resource Clamping (Vector 128) & Core Dump Leak (Vector 141)
    try:
        import resource  # noqa: PLC0415
        # Clamp virtual memory to 4GB
        resource.setrlimit(resource.RLIMIT_AS, (4 * 1024**3, 4 * 1024**3))
        # Disable core dumps
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    except (ImportError, ValueError, OSError):
        # Non-Linux or permission restricted
        pass

    # Verify directories exist before running any command
    ensure_dirs()

    parser = build_parser()
    args = parser.parse_args(argv)
    if hasattr(args, "func"):
        _safe_run(args.func, args)
    else:
        parser.print_help()


def _safe_run(func: Any, args: Any) -> None:  # noqa: ANN401
    """Run a CLI command with full error containment.

    Catches all unhandled exceptions, logs them via FlightRecorder,
    and exits cleanly with a user-friendly message instead of a raw traceback.
    """
    try:
        func(args)
    except KeyboardInterrupt:
        print("\n⛔ Interrupted by user.", file=sys.stderr)
        sys.exit(130)
    except SystemExit:
        raise  # Let sys.exit() pass through
    except Exception as e:
        from antigravity_harness.phoenix import FlightRecorder  # noqa: PLC0415

        recorder = FlightRecorder.instance()
        recorder.record_error(f"CLI.{func.__name__}", e, severity="FATAL")
        log_path = recorder.flush()

        print(f"\n🛑 FATAL ERROR in '{func.__name__}': {type(e).__name__}: {e}", file=sys.stderr)
        if log_path:
            print(f"📋 Flight log saved: {log_path}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    # HYDRA GUARD: Root Execution Guard (Vector 90)
    # Never run as root to avoid systemic damage or privilege escalation
    import os
    if hasattr(os, "getuid") and os.getuid() == 0:
        print("❌ SECURITY VIOLATION: Harness cannot be run as ROOT. Exiting for safety.")
        sys.exit(1)
        
    main()
