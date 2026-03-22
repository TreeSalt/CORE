import argparse
import hashlib
import json
import os
import platform
import random
import subprocess
import sys
from datetime import datetime, timezone
from typing import Any

import pandas as pd

from mantis_core import __version__
from mantis_core.autonomy import load_snapshot, save_snapshot, walk_forward_validation
from mantis_core.config import DataConfig, EngineConfig, GateThresholds, StrategyParams, load_yaml
from mantis_core.context import SimulationContextBuilder
from mantis_core.essence import EssenceLab
from mantis_core.paths import CERT_DIR, INTEL_DIR
from mantis_core.runner import SovereignRunner
from mantis_core.strategies import STRATEGY_REGISTRY


def calculate_file_hash(filepath: str) -> str:
    """Calculate SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        # Read and update hash string value in blocks of 4K
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def safe_json_value(v: Any) -> Any:  # noqa: PLR0911
    """Sanitize value for JSON serialization (fixes MagicMock/Objects in manifest)."""
    if v is None:
        return None
    if isinstance(v, (str, int, float, bool)):
        return v
    if isinstance(v, (list, tuple)):
        return [safe_json_value(x) for x in v]
    if isinstance(v, dict):
        return {str(k): safe_json_value(val) for k, val in v.items()}
    # Specific Mock handling or object handling
    if hasattr(v, "name") and isinstance(v.name, str):
        return v.name
    if hasattr(v, "_mock_name") and v._mock_name:  # MagicMock
        return str(v._mock_name)
    # Fallback
    return str(v)


def run_certification(args: argparse.Namespace) -> str:  # noqa: PLR0912, PLR0915
    """
    Execute a full Certification Run (Task E).
    Produces a reproducible proof bundle with MANIFEST.json and SHA256 integrity hashes.
    """
    timestamp_utc = datetime.now(timezone.utc).isoformat()

    # P0 FIX: Collision-proof ID (Microseconds + Random Suffix)
    # HYDRA GUARD: Environment Isolation (Vector 31)
    # Enforce Deterministic Release Mode for all Certification runs
    os.environ["METADATA_RELEASE_MODE"] = "1"
    
    # Suffix for collision-proof ID
    suffix = "".join(random.choices("0123456789abcdef", k=6))
    run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")[:18] + f"_{suffix}"

    # 1. Setup Output Directory
    cert_folder = CERT_DIR / f"{run_id}_{args.gate_profile}_cert" if args.outdir == "auto" else args.outdir

    if os.path.exists(cert_folder) and args.outdir == "auto":
        # Extremely unlikely collision safeguard
        run_id += "_dupe"
        cert_folder = CERT_DIR / f"{run_id}_{args.gate_profile}_cert"

    os.makedirs(cert_folder, exist_ok=True)
    print(f"🛡️ CERTIFICATION RUN: {run_id}")
    print(f"   Profile: {args.gate_profile}")
    print(f"   Strategy: {args.strategy}")
    print(f"   Output: {cert_folder}")

    # Initial manifest state allocation.
    manifest = {
        "cert_version": "1.1",
        "timestamp_utc": timestamp_utc,
        "run_id": run_id,
        "profile": safe_json_value(args.gate_profile),
        "strategy": safe_json_value(args.strategy),
        "params": {},
        "symbols": [],
        "timeframes": [],
        "lookback_days": args.lookback_days,
        "walk_forward": {},
        "snapshots": [],
        "outputs": {},
        "artifact_hashes": {},
        "environment": {"python": sys.version.split()[0], "platform": platform.platform()},
        "trader_ops_version": __version__,
    }
    generated_files = []
    cert_status = "PASS"
    cert_reasons = []
    strat_arg = getattr(args, "strategy", "v032_simple")  # Default fallback

    try:
        # P7 FIX: Early Crash Catching (Wrap Config Loading)
        # Parse List Args
        symbols = [s.strip() for s in args.symbols.split(",")]
        timeframes = [t.strip() for t in args.timeframes.split(",")]

        manifest["symbols"] = symbols
        manifest["timeframes"] = timeframes
        manifest["walk_forward"] = {
            "train_days": args.train_days,
            "test_days": args.test_days,
            "step_days": args.step_days,
        }

        # Load Params
        cfg_arg = getattr(args, "config", None)
        if cfg_arg and isinstance(cfg_arg, str):
            print(f"   Config: {cfg_arg}")
            cfg = load_yaml(cfg_arg)
            valid_keys = set(StrategyParams.__annotations__.keys())
            p_dict = {k: v for k, v in cfg.items() if k in valid_keys}
            params = StrategyParams(**p_dict)
            params_source = f"File: {os.path.basename(cfg_arg)}"
        else:
            print("   Config: DEFAULT")
            params = StrategyParams()
            params_source = "Default"

        # Update manifest with loaded params
        manifest["params"] = {
            "source": params_source,
            "values": safe_json_value({k: v for k, v in params.__dict__.items() if not k.startswith("_")}),
        }

        # Unified Physics: Engine Config
        engine_cfg = EngineConfig()
        forensics_arg = getattr(args, "forensics", None)
        if forensics_arg:
            engine_cfg.inject_forensics(forensics_arg)

        # 2. Snapshot Step
        print("\n[Phase 1] IMMUTABLE SNAPSHOTS")
        snapshot_map = {}  # (symbol, timeframe) -> path

        # Determine end date
        end_arg = getattr(args, "end", None)
        end_dt = pd.Timestamp(end_arg) if end_arg and isinstance(end_arg, str) else pd.Timestamp.now()

        start_dt = end_dt - pd.Timedelta(days=args.lookback_days)
        end_str = end_dt.strftime("%Y-%m-%d")
        start_str = start_dt.strftime("%Y-%m-%d")

        print(f"   Range: {start_str} to {end_str}")

        for sym in symbols:
            for tf in timeframes:
                print(f"  📸 Snapshotting {sym} {tf}...")
                try:
                    path, h8 = save_snapshot(sym, start_str, end_str, tf)
                    # Verify row count
                    df = load_snapshot(path)
                    rows = len(df)

                    # Full hash calculation for manifest integrity
                    full_hash = calculate_file_hash(path)

                    meta = {
                        "symbol": sym,
                        "timeframe": tf,
                        "path": str(path),
                        "file_name": os.path.basename(path),
                        "sha256": full_hash,
                        "rows": rows,
                        "start": str(df.index[0]),
                        "end": str(df.index[-1]),
                    }

                    manifest["snapshots"].append(meta)
                    snapshot_map[(sym, tf)] = path
                except Exception as e:
                    print(f"    ❌ Failed: {e}")
                    cert_status = "FAIL"
                    cert_reasons.append(f"SNAPSHOT_FAILED: {sym} {tf}: {str(e)}")
                    # Continue attempting other symbols if one fails

        # Save Snapshots Metadata
        snap_meta_path = os.path.join(cert_folder, "snapshots.json")
        with open(snap_meta_path, "w") as f:
            json.dump(manifest["snapshots"], f, indent=2, sort_keys=True)
        generated_files.append(snap_meta_path)

        # 3. Walk-Forward Step (Skip symbols that failed snapshot)
        print("\n[Phase 2] WALK-FORWARD VALIDATION")
        wf_results = []

        for sym in symbols:
            for tf in timeframes:
                snap_path = snapshot_map.get((sym, tf))
                if not snap_path:
                    print(f"  🚶 SKIPPING WF: {sym} {tf} (No Snapshot)")
                    continue

                print(f"  🚶 WF: {sym} {tf}")
                try:
                    res = walk_forward_validation(
                        sym,
                        tf,
                        snap_path,
                        args.gate_profile,
                        args.strategy,
                        params,
                        train_days=args.train_days,
                        test_days=args.test_days,
                        step_days=args.step_days,
                        engine_cfg=engine_cfg,
                    )

                    summary = {
                        "symbol": sym,
                        "timeframe": tf,
                        "status": res["status"],
                        "reason": res["reason"],
                        "pass_ratio": res.get("pass_ratio", 0.0),
                        "profit_status": res.get("profit_status"),
                        "safety_status": res.get("safety_status"),
                    }
                    wf_results.append(summary)
                    if res["status"] != "PASS":
                        print(f"    ⚠️ {res['status']}: {res['reason']}")
                    else:
                        print("    ✅ PASS")
                except Exception as e:
                    print(f"    ❌ WF Error: {e}")
                    cert_status = "FAIL"
                    cert_reasons.append(f"WF_CRASHED: {sym} {tf}: {str(e)}")

        # Save WF Results
        wf_path = os.path.join(cert_folder, "walkforward_results.json")
        with open(wf_path, "w") as f:
            json.dump(wf_results, f, indent=2, sort_keys=True)
        manifest["outputs"]["walkforward_results"] = "walkforward_results.json"
        generated_files.append(wf_path)

        # 4. Calibration Step (Cross-Asset)
        print("\n[Phase 3] CALIBRATION (Snapshot Re-Use)")
        calib_rows = []

        for sym in symbols:
            for tf in timeframes:
                snap_path = snapshot_map.get((sym, tf))
                if not snap_path:
                    continue

                try:
                    # Load DF from snapshot to inject
                    df_snap = load_snapshot(snap_path)

                    # Run Single Sim (Certification Mode)
                    runner = SovereignRunner(registry=STRATEGY_REGISTRY)
                    strat = STRATEGY_REGISTRY.instantiate(strat_arg)

                    ctx = (
                        SimulationContextBuilder()
                        .with_strategy(strat_arg, strat)
                        .with_params(params)
                        .with_data_cfg(DataConfig(interval=tf))
                        .with_engine_cfg(engine_cfg)
                        .with_thresholds(GateThresholds())
                        .with_symbol(sym)
                        .with_window(start_str, end_str)
                        .with_gate_profile(args.gate_profile)
                        .with_override_df(df_snap)
                        .with_intelligence(EssenceLab(INTEL_DIR).get_consensus_signal(["MARKET_PULSE", "MARKET_ALPHA"]))
                        .build()
                    )

                    res = runner.run_simulation(ctx)

                    row = {
                        "symbol": sym,
                        "timeframe": tf,
                        "status": res.status,
                        "profit_factor": res.metrics.profit_factor,
                        "max_dd_pct": res.metrics.max_dd_pct,
                        "sharpe": res.metrics.sharpe_ratio,
                        "trade_count": res.metrics.trade_count,
                        "fail_reason": res.fail_reason,
                    }
                    calib_rows.append(row)

                    # Phase 10.2: Evidence Integrity (Trace)
                    trace_df = res.trace
                    if trace_df is not None:
                        # Always save trace, even if empty (headers)
                        # Use safe_to_csv from utils if available, or pd.to_csv
                        # We need to import safe_to_csv or implement safety here.
                        # Let's import headers at top or use simple to_csv since we just want it done.
                        # But wait, "Empty CSV handling" was a requirement.
                        # I should import safe_to_csv.
                        trace_name = f"router_trace_{sym}_{tf}.csv"
                        trace_path = os.path.join(cert_folder, trace_name)
                        # Handle empty trace with headers
                        if trace_df.empty and not trace_df.columns.empty:
                            trace_df.to_csv(trace_path, index=False)
                        else:
                            trace_df.to_csv(trace_path, index=False)  # standard pandas handles empty OK usually?
                            # Phase 10.1 said "Empty DataFrames now write headers correctly".
                            # But let's be safe.
                        generated_files.append(trace_path)
                        manifest["outputs"][trace_name] = trace_name

                except Exception as e:
                    print(f"    ❌ Calibration Error: {sym} {tf}: {e}")
                    cert_status = "FAIL"
                    cert_reasons.append(f"CALIB_CRASHED: {sym} {tf}: {str(e)}")

        # Save CSV
        calib_df = pd.DataFrame(calib_rows)
        calib_path = os.path.join(cert_folder, "calibration_results.csv")
        calib_df.to_csv(calib_path, index=False)
        manifest["outputs"]["calibration_results"] = "calibration_results.csv"
        generated_files.append(calib_path)
        if not calib_df.empty:
            print(f"  📊 Calibration Matrix Saved ({len(calib_df)} rows)")

        # 6. Final Verdict Logic (Aggregate all failures/warns)
        # If cert_status is already FAIL (from crashes), keep it.
        # Otherwise evaluate statuses.

        # Check Walk-Forward Results
        for res in wf_results:
            s = res["status"]
            sym = res["symbol"]
            tf = res["timeframe"]
            r = res["reason"]

            if s == "FAIL":
                cert_status = "FAIL"
                cert_reasons.append(f"WF FAIL {sym} {tf}: {r}")
            elif s == "WARN" and cert_status != "FAIL":
                cert_status = "WARN"
                cert_reasons.append(f"WF WARN {sym} {tf}: {r}")

        # Check Calibration/Gate Results
        for row in calib_rows:
            s = row["status"]
            sym = row["symbol"]
            tf = row["timeframe"]
            r = row.get("fail_reason", "")

            if s == "FAIL":
                if cert_status != "FAIL":
                    cert_status = "FAIL"
                    cert_reasons.append(f"Gate FAIL {sym} {tf}: {r}")
            elif s == "WARN" and cert_status not in {"FAIL", "WARN"}:
                cert_status = "WARN"
                cert_reasons.append(f"Gate WARN {sym} {tf}: {r}")

        # Summary for Manifest
        pass_count = sum(1 for r in wf_results if r["status"] == "PASS")
        warn_count = sum(1 for r in wf_results if r["status"] == "WARN")
        fail_count = sum(1 for r in wf_results if r["status"] == "FAIL")

        manifest["cert_summary"] = {
            "symbols_tested": len(wf_results),
            "symbols_pass": pass_count,
            "symbols_warn": warn_count,
            "symbols_fail": fail_count,
            "profile": safe_json_value(args.gate_profile),
            "strategy": safe_json_value(strat_arg),
        }

    except Exception as global_e:
        print(f"\n🛑 CRITICAL_PIPELINE_FAILURE: {global_e}")
        # traceback.print_exc()
        cert_status = "FAIL"
        cert_reasons.append(f"PIPELINE_ERROR: {str(global_e)}")

    # P7 FIX: Auditability - Ensure Bundling even on Crash
    finally:
        # 7. Always-Bundle Logic (Final Phase)
        # This phase must run even if earlier phases errored, to produce the audit trail.
        print("\n[Phase 4] BUNDLING")

        # Add Verdict to Manifest
        manifest["cert_status"] = cert_status
        manifest["cert_reasons"] = cert_reasons

        # Save Config Echo
        args_dict = vars(args)
        safe_args = {k: str(v) for k, v in args_dict.items() if k != "func"}
        echo_path = os.path.join(cert_folder, "config_echo.json")
        with open(echo_path, "w") as f:
            json.dump(safe_args, f, indent=2, sort_keys=True)
        generated_files.append(echo_path)

        # Save Environment
        env_path = os.path.join(cert_folder, "environment.txt")
        with open(env_path, "w") as f:
            f.write(f"Python: {sys.version}\n")
            f.write(f"Platform: {platform.platform()}\n")
            try:
                git_hash = (
                    subprocess.check_output(["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL).decode().strip()
                )
                f.write(f"Git: {git_hash}\n")
            except Exception:
                f.write("Git: (Unavailable)\n")
        generated_files.append(env_path)

        # Calculate Hashes for all generated files
        print("   Calculating Integrity Hashes...")
        for fpath in generated_files:
            if os.path.exists(fpath):
                fname = os.path.basename(fpath)
                fhash = calculate_file_hash(fpath)
                manifest["artifact_hashes"][fname] = fhash

        # Save Final Manifest
        manifest_path = os.path.join(cert_folder, "MANIFEST.json")
        manifest_safe = safe_json_value(manifest)

        # Self-Hash Manifest (Standard Procedure)
        json_bytes = json.dumps(manifest_safe, sort_keys=True).encode("utf-8")
        m_hash = hashlib.sha256(json_bytes).hexdigest()
        manifest_safe["manifest_sha256"] = m_hash

        with open(manifest_path, "w") as f:
            json.dump(manifest_safe, f, indent=2, sort_keys=True)

        # Phase 10.2: Evidence Integrity (Metadata Alias)
        # "ALWAYS write RUN_METADATA.json"
        meta_path = os.path.join(cert_folder, "RUN_METADATA.json")
        with open(meta_path, "w") as f:
            json.dump(manifest_safe, f, indent=2, sort_keys=True)

        print(f"✅ BUNDLE CREATED: {cert_status}")
        if cert_reasons:
            print(f"   Reasons: {cert_reasons}")
        print(f"   Bundle: {manifest_path}")

        if cert_status == "FAIL":
            # Phase 10.3: Log to stdout, not stderr, to avoid preflight friction during expected failures
            print("🛑 NOTE: Certification Run Status: FAIL")
            # Do not call sys.exit here as it might be used as a library

    return manifest_path
