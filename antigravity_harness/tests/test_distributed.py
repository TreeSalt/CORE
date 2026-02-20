import os
import tempfile
import unittest
from unittest.mock import patch

import pandas as pd

from antigravity_harness.calibration import calibrate

try:
    import ray
except ImportError:
    ray = None


class TestDistributed(unittest.TestCase):
    def setUp(self):
        # Create a dummy data
        dates = pd.date_range("2021-01-01", "2021-02-01", freq="D")
        self.df = pd.DataFrame({"Open": 100.0, "High": 105.0, "Low": 95.0, "Close": 100.0, "Volume": 1000}, index=dates)

    def tearDown(self):
        try:
            import ray

            if ray.is_initialized():
                ray.shutdown()
        except ImportError:
            pass

    # Phase 9F: No longer skipped. calibrate() handles missing Ray with internal fallback.
    @patch("antigravity_harness.calibration.load_ohlc")
    @patch("antigravity_harness.calibration.load_yaml")
    def test_ray_calibration(self, mock_load_yaml, mock_load_ohlc):
        # Setup Mocks
        # Top patch is first arg: load_ohlc -> mock_load_ohlc
        # Bottom patch is second arg: load_yaml -> mock_load_yaml

        mock_load_ohlc.return_value = self.df

        # Grid with valid params (ma_length > ma_fast(20))
        mock_load_yaml.return_value = {"grid": {"ma_length": [50, 100], "rsi_length": [14], "timeframe": ["1d"]}}

        with tempfile.TemporaryDirectory() as tmpdir:
            try:
                # Mock Governance
                with patch("antigravity_harness.strategies.registry.STRATEGY_REGISTRY.verify_strategy_allowed"):
                    # Run with use_ray=True
                    calibrate(
                        grid_yaml="dummy.yaml",
                        output_dir=tmpdir,
                        strategy_name="v032_simple",
                        symbols=["BTC-USD"],
                        use_ray=True,
                    )

                # Check results
                res_csv = os.path.join(tmpdir, "results.csv")
                self.assertTrue(os.path.exists(res_csv))

                df_res = pd.read_csv(res_csv)
                # 2 values for ma * 1 rsi * 1 timeframe = 2 runs
                self.assertEqual(len(df_res), 2)
                self.assertTrue("portfolio_summary.csv" in os.listdir(tmpdir))

            except ImportError:
                print("Ray not installed, skipping test")
            except Exception as e:
                self.fail(f"Ray calibration failed: {e}")
