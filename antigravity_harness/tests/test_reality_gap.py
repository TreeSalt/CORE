import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from antigravity_harness.reality_gap import SchemaError, run_reality_gap


class TestRealityGap(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = Path(tempfile.mkdtemp(prefix="test_reality_gap_"))
        self.test_dir = self.tmp_dir / "reports"
        self.test_dir.mkdir(parents=True, exist_ok=True)
        
        # Inline fixture generation
        self.fills_path = self.tmp_dir / "fills.csv"
        self.signals_path = self.tmp_dir / "signals.csv"
        
        fills_df = pd.DataFrame([
            {"symbol": "BTC-USD", "side": "BUY", "qty": 1.0, "fill_price": 101.0, "fill_ts": "2026-01-01T00:30:00Z", "fee": 0.10},
            {"symbol": "BTC-USD", "side": "SELL", "qty": 1.0, "fill_price": 99.0, "fill_ts": "2026-01-01T01:00:00Z", "fee": 0.10},
        ])
        signals_df = pd.DataFrame([
            {"symbol": "BTC-USD", "side": "BUY", "qty": 1.0, "expected_price": 100.0, "signal_ts": "2026-01-01T00:00:00Z", "model_fee": 0.10},
            {"symbol": "BTC-USD", "side": "SELL", "qty": 1.0, "expected_price": 100.0, "signal_ts": "2026-01-01T00:45:00Z", "model_fee": 0.10},
        ])
        fills_df.to_csv(self.fills_path, index=False)
        signals_df.to_csv(self.signals_path, index=False)

    def tearDown(self):
        if self.tmp_dir.exists():
            shutil.rmtree(self.tmp_dir)

    def test_reality_gap_calculation(self):
        # 1. Run Reality Gap
        report_path = run_reality_gap(str(self.fills_path), str(self.signals_path), str(self.test_dir))

        # 2. Verify JSON Output
        self.assertTrue(os.path.exists(report_path))
        with open(report_path, "r") as f:
            data = json.load(f)

        stats = data.get("stats", {})

        # Assertions
        self.assertIn("matched_rows", stats)
        self.assertIn("fills_rows", stats)
        self.assertIn("signals_rows", stats)
        self.assertIn("slippage_bps_median", stats)
        self.assertIn("latency_sec_median", stats)

        # Check matched count
        self.assertEqual(stats["matched_rows"], 2)

    def test_schema_error(self):
        # Create a bad CSV
        bad_csv = self.test_dir / "bad_fills.csv"
        pd.DataFrame([{"wrong": 1}]).to_csv(bad_csv, index=False)

        with self.assertRaises(SchemaError):
            run_reality_gap(str(bad_csv), str(self.signals_path), str(self.test_dir))


if __name__ == "__main__":
    unittest.main()
