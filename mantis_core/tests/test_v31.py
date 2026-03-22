import os
import unittest
from unittest.mock import MagicMock, patch

import pandas as pd

from mantis_core.cli import build_parser
from mantis_core.paths import DATA_DIR, REPO_ROOT, REPORT_DIR
from mantis_core.registry import promote_to_staging


class TestV31(unittest.TestCase):
    def test_paths_determinism(self) -> None:
        # A simple check that paths are absolute and structure matches
        self.assertTrue(os.path.isabs(str(REPO_ROOT)))
        self.assertTrue(str(DATA_DIR).startswith(str(REPO_ROOT)))
        self.assertTrue(str(REPORT_DIR).startswith(str(REPO_ROOT)))

    def test_registry_anchor_immutability(self) -> None:
        # Setup temporary registry file patch
        # We need to mock registry saving/loading to avoid real IO drift

        mock_reg = {}

        with (
            patch("mantis_core.registry.load_registry", return_value=mock_reg),
            patch("mantis_core.registry.save_registry") as mock_save,
        ):
            # 1. First Promotion
            c1 = {"profit_factor": 2.0, "max_dd_pct": 0.1}
            promote_to_staging("TEST", "1h", c1)

            # Capture what was saved
            saved_1 = mock_save.call_args[0][0]
            anchor_1 = saved_1["TEST_1h"]["anchor_metrics"]
            self.assertEqual(anchor_1["profit_factor"], 2.0)

            # 2. Second Promotion (Higher PF, but NO reset)
            # Mock reg needs to be updated manually since we mocked load/save
            mock_reg.update(saved_1)

            c2 = {"profit_factor": 2.5, "max_dd_pct": 0.1}
            promote_to_staging("TEST", "1h", c2, reset_anchor=False)

            saved_2 = mock_save.call_args[0][0]
            anchor_2 = saved_2["TEST_1h"]["anchor_metrics"]

            # Anchor should STILL be c1 (2.0)
            self.assertEqual(anchor_2["profit_factor"], 2.0)
            self.assertEqual(saved_2["TEST_1h"]["metrics"]["profit_factor"], 2.5)

            # 3. Third Promotion (Reset Anchor)
            mock_reg.update(saved_2)
            promote_to_staging("TEST", "1h", c2, reset_anchor=True)

            saved_3 = mock_save.call_args[0][0]
            anchor_3 = saved_3["TEST_1h"]["anchor_metrics"]

            # Anchor should now be c2 (2.5)
            self.assertEqual(anchor_3["profit_factor"], 2.5)

    def test_cli_renaming(self) -> None:
        p = build_parser()

        # Test stage-candidate arg parsing
        args = p.parse_args(["stage-candidate", "--symbol", "BTC", "--reset-anchor"])
        self.assertTrue(args.reset_anchor)
        self.assertEqual(args.cmd, "stage-candidate")

        # Test deprecated alias
        args_old = p.parse_args(["update-champion", "--symbol", "BTC"])
        self.assertEqual(args_old.cmd, "update-champion")
        # Func should be same
        self.assertEqual(args.func, args_old.func)

    @patch("mantis_core.certification.calculate_file_hash")
    @patch("mantis_core.certification.save_snapshot")
    @patch("mantis_core.certification.walk_forward_validation")
    @patch("mantis_core.certification.SovereignRunner")
    def test_certification_pipeline(self, mock_runner_cls, mock_wf, mock_snap, mock_hash):
        # Test logic flow of certify-run
        from mantis_core.certification import run_certification
        from mantis_core.models import MetricSet, SimulationResult

        # Mock returns
        mock_snap.return_value = ("/tmp/s.csv", "hash123")

        mock_instance = mock_runner_cls.return_value
        mock_instance.run_simulation.return_value = SimulationResult(
            params={},
            status="PASS",
            profit_status="PASS",
            safety_status="PASS",
            fail_reason="",
            warns=[],
            gate_results=[],
            metrics=MetricSet(profit_factor=2.0),
        )

        # Use simple args
        args = MagicMock()
        args.outdir = "auto"
        args.symbols = "BTC"
        args.timeframes = "4h"
        args.strategy = "v032_simple"
        args.gate_profile = "crypto_profit"
        args.train_days = 100
        args.test_days = 10
        args.step_days = 10
        args.lookback_days = 200

        # Mock load_snapshot to return dummy DF for row counting
        with patch("mantis_core.certification.load_snapshot") as mock_load:
            mock_load.return_value = pd.DataFrame({"Close": [100]}, index=pd.to_datetime(["2021-01-01"]))

            mock_wf.return_value = {"status": "PASS", "reason": "OK"}

            # Run
            # We need to mock os.makedirs and json.dump to avoid real FS writes
            # Run
            # We need to mock os.makedirs and json.dump to avoid real FS writes
            with (
                patch("os.makedirs"),
                patch("builtins.open", unittest.mock.mock_open()),
                patch("json.dump"),
                patch("pandas.DataFrame.to_csv"),
                patch("mantis_core.strategies.registry.STRATEGY_REGISTRY.verify_strategy_allowed"),
            ):
                run_certification(args)

        # Verify calls
        mock_snap.assert_called()
        mock_wf.assert_called()

    @patch("mantis_core.autonomy.load_snapshot")
    @patch("mantis_core.autonomy.SovereignRunner")
    def test_wf_intraday_precision(self, mock_runner_cls, mock_load):
        from mantis_core.autonomy import walk_forward_validation
        from mantis_core.config import StrategyParams
        from mantis_core.models import MetricSet, SimulationResult

        # Setup Data: 10 days of 4h data
        dates = pd.date_range("2021-01-01", "2021-01-10", freq="4h")
        df = pd.DataFrame({"Close": [100] * len(dates)}, index=dates)
        mock_load.return_value = df

        mock_instance = mock_runner_cls.return_value
        mock_instance.run_simulation.return_value = SimulationResult(
            params={},
            status="PASS",
            profit_status="PASS",
            safety_status="PASS",
            fail_reason="",
            warns=[],
            gate_results=[],
            metrics=MetricSet(profit_factor=2.0),
        )

        # Run WF with small windows
        # Train 1 day, Test 1 day
        # Run WF with small windows
        # Train 1 day, Test 1 day
        with patch("mantis_core.strategies.registry.STRATEGY_REGISTRY.verify_strategy_allowed"):
            walk_forward_validation(
                "BTC",
                "4h",
                "dummy_path",
                "test_prof",
                "v032_simple",
                StrategyParams(),
                train_days=1,
                test_days=1,
                step_days=1,
            )

        # Check assertions
        self.assertTrue(mock_instance.run_simulation.called)
        call_args = mock_instance.run_simulation.call_args

        # Verify Context
        ctx = call_args.args[0]
        start_arg = ctx.start
        end_arg = ctx.end

        # Verify precision (contains 'T' or ':')
        self.assertIn("T", start_arg, f"Start '{start_arg}' lacks time precision")
        self.assertIn("T", end_arg, f"End '{end_arg}' lacks time precision")


if __name__ == "__main__":
    unittest.main()
