import contextlib
import io
import unittest
from unittest.mock import MagicMock, patch

# Import the module under test
# We need to make sure the import path is correct
# We need to make sure the import path is correct
# sys.path.append("01_ENGINE") - REMOVED (Flattened structure)
from antigravity_harness import cli
from antigravity_harness.models import MetricSet, SimulationResult


class TestCliAlias(unittest.TestCase):
    def setUp(self) -> None:
        self.parser = cli.build_parser()

    @patch("antigravity_harness.cli.save_snapshot")
    @patch("antigravity_harness.cli.walk_forward_validation")
    @patch("antigravity_harness.cli.promote_to_staging")
    @patch("antigravity_harness.cli.load_snapshot")
    @patch("antigravity_harness.cli._run_one")
    def test_update_champion_alias_execution(self, mock_run_one, mock_load_snap, mock_promote, mock_wf, mock_save_snap):
        """
        TASK 1: Verify 'update-champion' alias does not crash and behaves like 'stage-candidate'.
        """
        # Mock returns
        mock_save_snap.return_value = ("/tmp/mock_snap.pkl", "abcdef1234567890")
        mock_wf.return_value = {"status": "PASS", "pass_ratio": 0.9, "reason": "Good"}
        mock_load_snap.return_value = MagicMock()  # Mock DF
        mock_run_one.return_value = SimulationResult(
            params={},
            status="PASS",
            profit_status="PASS",
            safety_status="PASS",
            fail_reason="",
            warns=[],
            gate_results=[],
            metrics=MetricSet(profit_factor=2.5, max_dd_pct=0.1, sharpe_ratio=1.5, trade_count=100),
        )
        mock_promote.return_value = {"status": "PASS", "message": "Promoted"}

        # Args that previously crashed update-champion
        cmd_args = [
            "update-champion",
            "--symbol",
            "BTC-USD",
            "--strategy",
            "v032_simple",
            "--start",
            "2020-01-01",
            "--end",
            "2021-01-01",
            "--gate-profile",
            "crypto_profit",
        ]

        # Parse
        args = self.parser.parse_args(cmd_args)

        # Execute (should not raise AttributeError)
        with patch("sys.stdout", new=io.StringIO()) as fake_out:
            with patch("antigravity_harness.strategies.registry.STRATEGY_REGISTRY.verify_strategy_allowed"):
                with contextlib.suppress(SystemExit):
                    args.func(args)
            output = fake_out.getvalue()

        # Assertions
        self.assertIn("WARNING: 'update-champion' is deprecated", output)
        self.assertEqual(args.cmd, "update-champion")
        self.assertEqual(args.symbol, "BTC-USD")

        # Verify flow called correct mocks
        mock_save_snap.assert_called_once()
        mock_wf.assert_called_once()
        mock_promote.assert_called_once()

    @patch("antigravity_harness.cli.save_snapshot")
    @patch("antigravity_harness.cli.walk_forward_validation")
    @patch("antigravity_harness.cli.promote_to_staging")
    @patch("antigravity_harness.cli.load_snapshot")
    @patch("antigravity_harness.cli._run_one")
    def test_stage_candidate_single_sim(self, mock_run_one, mock_load_snap, mock_promote, mock_wf, mock_save_snap):
        """
        TASK 2: Verify 'stage-candidate' calls _run_one exactly ONCE using the snapshot.
        """
        # Mock returns
        mock_save_snap.return_value = ("/tmp/mock_snap.pkl", "hash123")
        mock_wf.return_value = {"status": "PASS", "pass_ratio": 0.9, "reason": "Good"}
        # Mock DF
        mock_df = MagicMock()
        mock_load_snap.return_value = mock_df

        mock_run_one.return_value = SimulationResult(
            params={},
            status="PASS",
            profit_status="PASS",
            safety_status="PASS",
            fail_reason="",
            warns=[],
            gate_results=[],
            metrics=MetricSet(profit_factor=2.0, max_dd_pct=0.15),
        )
        mock_promote.return_value = {"status": "PASS", "message": "Promoted"}

        cmd_args = ["stage-candidate", "--symbol", "ETH-USD"]

        args = self.parser.parse_args(cmd_args)

        with patch("sys.stdout", new=io.StringIO()), contextlib.suppress(SystemExit):
            with patch("antigravity_harness.strategies.registry.STRATEGY_REGISTRY.verify_strategy_allowed"):
                args.func(args)

        # Assertions
        # 1. _run_one called exactly ONCE
        self.assertEqual(mock_run_one.call_count, 1)

        # 2. _run_one called WITH the snapshot dataframe
        call_args = mock_run_one.call_args
        # Kwargs should contain snapshot_df
        self.assertIn("snapshot_df", call_args.kwargs)
        self.assertEqual(call_args.kwargs["snapshot_df"], mock_df)

        # 3. load_snapshot called
        mock_load_snap.assert_called_with("/tmp/mock_snap.pkl")


if __name__ == "__main__":
    unittest.main()
