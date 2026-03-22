import os
import subprocess
import sys
import unittest

import pandas as pd

# Add project root to path
# __file__ is antigravity_harness/tests/test_phase10_2_iron_gate.py
# parent is antigravity_harness/tests
# grandparent is antigravity_harness
# great-grandparent is v9e_stage (where antigravity_harness package lives)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from mantis_core import __version__
from mantis_core.portfolio_router import PortfolioRouter


class TestPhase10_2_IronGate(unittest.TestCase):
    def test_01_compilation(self):
        """Task 1: Compilation Gate"""
        print("\n[Iron Gate] Testing Compilation...")
        try:
            subprocess.check_call([sys.executable, "-m", "compileall", "-q", "."])
            print("  ✅ Compileall passed.")
        except subprocess.CalledProcessError:
            self.fail("Compilation failed!")

    def test_02_version_truth(self):
        """Task 2: Version Kill Switch"""
        import re

        print("\n[Iron Gate] Testing Version Truth...")
        print(f"  Current Version: {__version__}")
        # Verify semantic versioning format (X.Y.Z)
        self.assertTrue(re.match(r"^\d+\.\d+\.\d+$", __version__), f"Invalid version format: {__version__}")

        # Verify we are at least at the Dragonproof baseline (4.4.0)
        major, minor, _ = map(int, __version__.split("."))
        self.assertTrue(major >= 4 and minor >= 4, f"Version too low for Dragonproof: {__version__}")

        # Grep for stale v4.x.4 (obfuscated)
        stale_ver = "v4" + ".2.4"
        result = subprocess.run(["grep", "-r", stale_ver, "."], capture_output=True, text=True, check=False)
        # Filter out binary files and this test script itself if it matched (but I didn't write it there)
        hits = [
            line
            for line in result.stdout.splitlines()
            if not line.startswith("Binary file")
            and "test_phase10_2_iron_gate.py" not in line
            and "build_log.txt" not in line
            and "__pycache__" not in line
        ]

        if hits:
            print(f"  ❌ Found stale '{stale_ver}' strings:")
            for h in hits:
                print(f"    {h}")
            self.fail("Found stale version strings!")
        else:
            print(f"  ✅ No stale '{stale_ver}' found.")

    def test_03_physics_hardening(self):
        """Task 4: Physics Hardening (Portfolio)"""
        print("\n[Iron Gate] Testing Physics Hardening...")

        # Case 1: 1d -> 365
        r1 = PortfolioRouter(interval="1d")
        self.assertEqual(r1.policy_cfg.periods_per_year, 365, "1d should be 365")

        # Case 2: 4h -> 2190
        # Policy defaulted to 365, but router should override it
        r2 = PortfolioRouter(interval="4h")
        self.assertEqual(r2.policy_cfg.periods_per_year, 2190, "4h should be 2190")
        print(f"  ✅ 4h Correctly scaled to {r2.policy_cfg.periods_per_year}")

        # Case 3: 15m -> 35040
        r3 = PortfolioRouter(interval="15m")
        self.assertEqual(r3.policy_cfg.periods_per_year, 35040, "15m should be 35040")

    def test_04_trace_integrity(self):
        """Task 3: Evidence Integrity (Trace Generation)"""
        print("\n[Iron Gate] Testing Trace Integrity (Zero-Trade)...")
        # We need to simulate a call that generates a trace.
        # run_backtest usually does it.
        from mantis_core.config import StrategyParams
        from mantis_core.engine import EngineConfig, run_backtest
        from mantis_core.strategies.base import Strategy

        # Mock class
        class MockStrategy(Strategy):
            def generate_signals(self, df):
                return pd.Series(0, index=df.index)  # No signals

            def prepare_data(self, df, params):
                # Engine expects certain columns
                df = df.copy()
                df["entry_signal"] = 0
                df["exit_signal"] = 0
                df["ATR"] = 1.0  # arbitrary
                return df

        # Mock Data
        dates = pd.date_range("2024-01-01", periods=10, freq="D")
        df = pd.DataFrame({"Open": 100, "High": 101, "Low": 99, "Close": 100, "Volume": 1000}, index=dates)

        strat = MockStrategy()
        prep = strat.prepare_data(df, None)
        res = run_backtest(df, prep, StrategyParams(), EngineConfig())

        self.assertIsInstance(res.trace, pd.DataFrame, "Trace is not a DataFrame")
        self.assertFalse(res.trace.empty, "Trace should not be empty (should have rows for each bar)")
        if "regime" in res.trace.columns:
            print("  ✅ Trace has regime column.")
        else:
            print("  ⚠️ Trace missing regime column (expected?)")

        # Verify Headers even if empty?
        # If we had 0 bars, trace might be empty.
        # But we had 10 bars.
        print(f"  ✅ Trace generated with {len(res.trace)} rows.")


if __name__ == "__main__":
    unittest.main()
