import argparse
import json
import uuid
from pathlib import Path

import pandas as pd
import yaml

from antigravity_harness.certification import run_certification
from antigravity_harness.reporting import save_run_metadata
from antigravity_harness.schema import GridConfig
from antigravity_harness.utils import safe_to_csv


def run_sweep(args: argparse.Namespace) -> None:  # noqa: PLR0912, PLR0915
    """
    Execute a Strategy Discovery Sweep (Task 2.1).
    Iterates through (Symbol x Timeframe x Config) combinations.
    """
    print("🧹 CERTIFICATION SWEEP")
    print(f"   Strategy: {args.strategy}")
    print(f"   Profile: {args.gate_profile}")

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    # 1. Expand Grid
    symbols = [s.strip() for s in args.symbols.split(",")]
    timeframes = [t.strip() for t in args.timeframes.split(",")]

    combinations = []  # List of (symbol, timeframe, params_dict, config_id)

    if args.config_grid:
        # Load grid from YAML
        with open(args.config_grid, "r") as f:
            grid_def = yaml.safe_load(f)

        # Support multiple grids in one file or single dict
        grids = grid_def if isinstance(grid_def, list) else [grid_def]

        for g in grids:
            # Convert to GridConfig object (simple version)
            # Current schema logic assumes a list of explicit configs or a grid definition.
            # We defer complex schema validation to the schema module.
            gc = GridConfig(strategy=args.strategy, params=g["params"])
            combos = gc.generate_combinations()
            for c in combos:
                combinations.append(c)
    else:
        # Default single config (empty params dict -> default)
        combinations.append({})

    print(f"   Combinations (Params): {len(combinations)}")
    total_runs = len(symbols) * len(timeframes) * len(combinations)
    print(f"   Total Runs: {total_runs}")

    results = []

    # 2. Iterate and Execute
    run_idx = 0
    for sym in symbols:
        for tf in timeframes:
            for params in combinations:
                run_idx += 1
                run_id = f"R{run_idx:04d}_{str(uuid.uuid4())[:8]}"
                print(f"\n--- Run {run_idx}/{total_runs} [{sym} {tf}] ---")

                # Create a specific config file for this run if params exist
                # We need to pass it via --config argument to certify-run
                # So we write a temporary config file
                config_path = None
                if params:
                    config_name = f"config_{run_id}.yaml"
                    config_path = outdir / "configs" / config_name
                    config_path.parent.mkdir(exist_ok=True)
                    with open(config_path, "w") as f:
                        yaml.dump(params, f, sort_keys=True)

                # Construct Args
                # We reuse the same args object but override specific fields
                # We reuse the same args object but override specific fields.
                # While a fresh namespace is cleaner, this overlay ensures args propagation.

                # We need to map `sweep` args to `certify-run` args
                # We use a copy of sweep args, then overlay

                cert_out = outdir / "runs" / run_id

                cert_args = argparse.Namespace(
                    symbols=sym,
                    timeframes=tf,
                    gate_profile=args.gate_profile,
                    strategy=args.strategy,
                    outdir=str(cert_out),
                    lookback_days=args.lookback_days,
                    train_days=args.train_days,
                    test_days=args.test_days,
                    step_days=args.step_days,
                    config=str(config_path) if config_path else None,
                    end=getattr(args, "end", None),
                )

                try:
                    manifest_path = run_certification(cert_args)

                    # 3. Harvest Result
                    with open(manifest_path, "r") as f:
                        m = json.load(f)

                    # Extract Summary
                    # We assume 1 symbol x 1 timeframe per run in this loop structure
                    # But certify-run supports multiple.
                    # Here we forced single.

                    row = {
                        "run_id": run_id,
                        "symbol": sym,
                        "timeframe": tf,
                        "cert_status": m.get("cert_status", "UNKNOWN"),
                        "cert_reasons": "; ".join(m.get("cert_reasons", [])),
                        "manifest_path": str(manifest_path),
                        "manifest_sha256": m.get("manifest_sha256", ""),
                    }

                    # Add Metrics from Internal Results if available
                    # We look into calibration_results or walkforward_results
                    # Let's peek at walkforward_results for pass_ratio
                    # The manifest has "outputs" paths
                    wf_rel = m.get("outputs", {}).get("walkforward_results")
                    if wf_rel:
                        wf_full = cert_out / wf_rel
                        if wf_full.exists():
                            with open(wf_full, "r") as f:
                                wf_data = json.load(f)
                                # Should be list of 1
                                if wf_data:
                                    w = wf_data[0]
                                    row["pass_ratio"] = w.get("pass_ratio")
                                    row["wf_status"] = w.get("status")
                                    row["safety_status"] = w.get("safety_status")
                                    row["profit_status"] = w.get("profit_status")

                    # Add Calibration Metrics
                    cal_rel = m.get("outputs", {}).get("calibration_results")
                    if cal_rel:
                        cal_full = cert_out / cal_rel
                        if cal_full.exists():
                            df_c = pd.read_csv(cal_full)
                            if not df_c.empty:
                                r = df_c.iloc[0]
                                row["profit_factor"] = r.get("profit_factor")
                                row["sharpe"] = r.get("sharpe")
                                row["max_dd_pct"] = r.get("max_dd_pct")
                                row["trade_count"] = r.get("trade_count")

                    results.append(row)

                except Exception as e:
                    print(f"❌ Run Failed: {e}")
                    results.append(
                        {
                            "run_id": run_id,
                            "symbol": sym,
                            "timeframe": tf,
                            "cert_status": "CRASH",
                            "cert_reasons": str(e),
                        }
                    )

    # 4. Save Aggregated Results
    df = pd.DataFrame(results)
    if not df.empty:
        # Sweep Results
        sweep_path = outdir / "sweep_results.csv"
        safe_to_csv(df, sweep_path, index=False)

        # Leaderboard (PASS/WARN only)
        leaderboard = df[df["cert_status"].isin(["PASS", "WARN"])].sort_values(
            by=["cert_status", "pass_ratio"], ascending=[True, False]
        )
        lb_path = outdir / "leaderboard.csv"
        safe_to_csv(leaderboard, lb_path, index=False)
        print(f"🏆 Leaderboard: {lb_path} ({len(leaderboard)} candidates)")

        # Forensics (Task 2.3)
        fail_reasons = []
        for r in df["cert_reasons"]:
            if pd.isna(r):
                continue
            fail_reasons.extend([x.strip() for x in str(r).split(";") if x.strip()])

        from collections import Counter  # noqa: PLC0415

        c = Counter(fail_reasons)
        breakdown_path = outdir / "failure_breakdown.csv"
        safe_to_csv(pd.DataFrame(c.most_common(), columns=["Reason", "Count"]), breakdown_path, index=False)
        print(f"🔍 Forensics: {breakdown_path}")

    save_run_metadata(outdir, config={"sweep_config": args.config_grid or "default_single"}, cmd_args=vars(args))

    print(f"\n✅ Sweep Complete. Output: {outdir}")
