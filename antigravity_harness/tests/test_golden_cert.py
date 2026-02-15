import argparse
import unittest
from unittest.mock import mock_open, patch

import pandas as pd

from antigravity_harness.certification import run_certification
from antigravity_harness.models import MetricSet, SimulationResult


class TestGoldenCert(unittest.TestCase):
    """
    Task 1.4: Golden Baseline Certification Test
    Verifies verdict logic and manifest integrity without network.
    """

    def setUp(self) -> None:
        self.args = argparse.Namespace(
            symbols="BTC-USD,ETH-USD",
            timeframes="4h",
            gate_profile="crypto_profit",
            strategy="v032_simple",
            outdir="auto",
            lookback_days=100,
            train_days=50,
            test_days=10,
            step_days=5,
            config=None,
            end="2025-01-01",
        )
        # Helper to create dummy result
        self.dummy_result = SimulationResult(
            params={},
            status="PASS",
            profit_status="PASS",
            safety_status="PASS",
            fail_reason="",
            warns=[],
            gate_results=[],
            metrics=MetricSet(
                profit_factor=2.0, max_dd_pct=0.1, sharpe_ratio=1.5, trade_count=10, gross_profit=100.0, gross_loss=50.0
            ),
            trace=pd.DataFrame(),
        )

    @patch("antigravity_harness.certification.calculate_file_hash")
    @patch("antigravity_harness.certification.save_snapshot")
    @patch("antigravity_harness.certification.walk_forward_validation")
    @patch("antigravity_harness.certification.SovereignRunner")
    @patch("antigravity_harness.certification.load_snapshot")
    @patch("pandas.DataFrame.to_csv")
    @patch("builtins.open", new_callable=mock_open)
    @patch("os.makedirs")
    @patch("json.dump")
    def test_verdict_fail_propagation(  # noqa: PLR0913
        self, mock_json, mock_makedirs, mock_file, mock_csv, mock_load, mock_runner_cls, mock_wf, mock_snap, mock_hash
    ):
        """Test Case: One symbol FAIL -> Cert FAIL"""
        # Setup Mocks
        mock_snap.return_value = ("/tmp/snap.csv", "hash123")
        mock_load.return_value = pd.DataFrame({"Close": [1.0]}, index=[pd.Timestamp("2024-01-01")])
        mock_hash.return_value = "sha256_mock"

        # Scenario: BTC fails, ETH passes
        def wf_side_effect(sym, *args, **kwargs):
            if sym == "BTC-USD":
                return {"status": "FAIL", "reason": "Too much drawdown"}
            return {"status": "PASS", "reason": "OK"}

        mock_wf.side_effect = wf_side_effect

        # Mock SovereignRunner instance
        mock_instance = mock_runner_cls.return_value
        mock_instance.run_simulation.return_value = self.dummy_result

        # Run
        run_certification(self.args)

        # Verify Manifest
        # We need to find the call to json.dump that saved the manifest
        # arguments to json.dump are (obj, file_handle, ...)

        manifest_found = None
        for call in mock_json.call_args_list:
            obj = call[0][0]
            if isinstance(obj, dict) and "cert_version" in obj:
                manifest_found = obj

        self.assertIsNotNone(manifest_found, "Manifest not dumped")

        # Assertions
        self.assertEqual(manifest_found["cert_status"], "FAIL")
        # Check that we found the reason string (partial match)
        found_reason = any("WF FAIL BTC-USD" in r for r in manifest_found.get("cert_reasons", []))
        self.assertTrue(found_reason, "Fail reason not found in manifest")

        self.assertTrue("manifest_sha256" in manifest_found)
        # Check summary
        self.assertEqual(manifest_found["cert_summary"]["symbols_fail"], 1)

    @patch("antigravity_harness.certification.calculate_file_hash")
    @patch("antigravity_harness.certification.save_snapshot")
    @patch("antigravity_harness.certification.walk_forward_validation")
    @patch("antigravity_harness.certification.SovereignRunner")
    @patch("antigravity_harness.certification.load_snapshot")
    @patch("pandas.DataFrame.to_csv")
    @patch("builtins.open", new_callable=mock_open)
    @patch("os.makedirs")
    @patch("json.dump")
    def test_verdict_warn_propagation(  # noqa: PLR0913
        self, mock_json, mock_makedirs, mock_file, mock_csv, mock_load, mock_runner_cls, mock_wf, mock_snap, mock_hash
    ):
        """Test Case: One symbol WARN, no FAIL -> Cert WARN"""
        mock_snap.return_value = ("/tmp/snap.csv", "hash123")
        mock_load.return_value = pd.DataFrame({"Close": [1.0]}, index=[pd.Timestamp("2024-01-01")])
        mock_hash.return_value = "sha256_mock"

        def wf_side_effect(sym, *args, **kwargs):
            if sym == "BTC-USD":
                return {"status": "WARN", "reason": "Slightly low PF"}
            return {"status": "PASS", "reason": "OK"}

        mock_wf.side_effect = wf_side_effect

        mock_instance = mock_runner_cls.return_value
        mock_instance.run_simulation.return_value = self.dummy_result

        run_certification(self.args)

        manifest_found = None
        for call in mock_json.call_args_list:
            obj = call[0][0]
            if isinstance(obj, dict) and "cert_version" in obj:
                manifest_found = obj

        self.assertIsNotNone(manifest_found, "Manifest not dumped")
        self.assertEqual(manifest_found["cert_status"], "WARN")
        found_reason = any("WF WARN BTC-USD" in r for r in manifest_found.get("cert_reasons", []))
        self.assertTrue(found_reason)

    @patch("antigravity_harness.certification.calculate_file_hash")
    @patch("antigravity_harness.certification.save_snapshot")
    @patch("antigravity_harness.certification.walk_forward_validation")
    @patch("antigravity_harness.certification.SovereignRunner")
    @patch("antigravity_harness.certification.load_snapshot")
    @patch("pandas.DataFrame.to_csv")
    @patch("builtins.open", new_callable=mock_open)
    @patch("os.makedirs")
    @patch("json.dump")
    def test_verdict_pass(  # noqa: PLR0913
        self, mock_json, mock_makedirs, mock_file, mock_csv, mock_load, mock_runner_cls, mock_wf, mock_snap, mock_hash
    ):
        """Test Case: All PASS -> Cert PASS"""
        mock_snap.return_value = ("/tmp/snap.csv", "hash123")
        mock_load.return_value = pd.DataFrame({"Close": [1.0]}, index=[pd.Timestamp("2024-01-01")])
        mock_hash.return_value = "sha256_mock"

        mock_wf.return_value = {"status": "PASS", "reason": "Great job"}

        mock_instance = mock_runner_cls.return_value
        mock_instance.run_simulation.return_value = self.dummy_result

        run_certification(self.args)

        manifest_found = None
        for call in mock_json.call_args_list:
            obj = call[0][0]
            if isinstance(obj, dict) and "cert_version" in obj:
                manifest_found = obj

        self.assertIsNotNone(manifest_found, "Manifest not dumped")
        self.assertEqual(manifest_found["cert_status"], "PASS")


if __name__ == "__main__":
    unittest.main()
