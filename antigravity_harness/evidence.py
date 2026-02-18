import json
import os
import subprocess
import sys
from pathlib import Path

import pandas as pd


class EvidenceForge:
    """
    The Evidence Forge: Runs deterministic smoke tests to generate and verify evidence artifacts.
    """

    def __init__(self, out_dir: str = "reports/forge/synthetic_smoke"):
        self.out_dir = Path(out_dir)

    def run(self) -> None:
        print("🔨 FORGE: Initiating Evidence Generation...")

        # 1. TRADER_OPS_SMOKE (Synthetic Equity Portfolio)
        cmd = [
            sys.executable,
            "-B",
            "-m",
            "antigravity_harness.cli",
            "portfolio-backtest",
            "--synthetic",
            "--symbols",
            "MOCK",  # Symbol binding required for command-line parsing.
            "--equity",  # Test Equity Validation (252 days)
            "--router",
            "regime_v1",
            "--outdir",
            str(self.out_dir),
        ]

        print(f"   Command: {' '.join(cmd)}")
        try:
            env = os.environ.copy()
            env["METADATA_RELEASE_MODE"] = "1"
            subprocess.run(cmd, check=True, env=env)
        except subprocess.CalledProcessError as e:
            print(f"❌ FAIL: Simulation crashed. {e}")
            sys.exit(1)

        # 2. Verify Artifacts
        self._verify_artifacts()

        print("✅ FORGE COMPLETE: Evidence Generated and Verified.")

    def _verify_artifacts(self) -> None:
        print("🔍 FORGE: Verifying Artifacts...")

        # 2.1 Router Trace
        trace_path = self.out_dir / "router_trace.csv"
        if not trace_path.exists():
            print("❌ FAIL: router_trace.csv missing")
            sys.exit(1)

        trace = pd.read_csv(trace_path)
        if trace.empty:
            print("⚠️ WARNING: router_trace.csv is empty (headers only). Check router logic.")
            print("❌ FAIL: router_trace.csv is empty")
            sys.exit(1)

        print(f"   ✅ router_trace.csv found ({len(trace)} rows)")

        # 2.2 Run Metadata
        meta_path = self.out_dir / "RUN_METADATA.json"
        if not meta_path.exists():
            print("❌ FAIL: RUN_METADATA.json missing")
            sys.exit(1)

        with open(meta_path) as f:
            meta = json.load(f)

        ppy = meta.get("periods_per_year")
        if ppy != 252:  # noqa: PLR2004
            print(f"❌ FAIL: Expected periods_per_year=252 (Equity), got {ppy}")
            sys.exit(1)

        print(f"   ✅ RUN_METADATA.json verified (Physics: {ppy})")

        # 2.3 Forensic FillTape
        tape_path = self.out_dir / "fill_tape.csv"
        if not tape_path.exists():
            print("❌ FAIL: fill_tape.csv missing (Execution Fidelity P2 violation)")
            sys.exit(1)

        tape = pd.read_csv(tape_path)
        if tape.empty:
            print("❌ FAIL: fill_tape.csv is empty")
            sys.exit(1)

        # Basic Check: ensure drift columns exist
        drift_cols = ["drift_pts", "drift_bps", "slippage_realized_ticks"]
        missing_cols = [c for c in drift_cols if c not in tape.columns]
        if missing_cols:
            print(f"❌ FAIL: fill_tape.csv missing drift columns: {missing_cols}")
            sys.exit(1)

        print(f"   ✅ fill_tape.csv verified ({len(tape)} fills, drift tracking active)")
