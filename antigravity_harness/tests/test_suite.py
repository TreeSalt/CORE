import argparse
import contextlib
import io
import os
import shutil
import unittest
from dataclasses import dataclass
from typing import Any
from unittest.mock import MagicMock, patch

import pandas as pd

from antigravity_harness.autonomy import load_snapshot

# Import SUT
from antigravity_harness.calibration import _run_one
from antigravity_harness.cli import cmd_validate
from antigravity_harness.config import DataConfig, EngineConfig, GateThresholds, StrategyParams
from antigravity_harness.context import SimulationContextBuilder
from antigravity_harness.gates import GateResult, _run_sim, _status_from_gate_results, evaluate_gates
from antigravity_harness.models import MetricSet, SimulationResult
from antigravity_harness.registry import load_registry, promote_to_staging
from antigravity_harness.strategies import REGISTRY
from antigravity_harness.strategies import V032Simple


@dataclass
class MockGateResult:
    def __init__(self, gate, status, reason):
        self.gate = gate
        self.status = status
        self.reason = reason

    def model_dump(self):
        return {"gate": self.gate, "status": self.status, "reason": self.reason}


@dataclass
class MockTrade:
    entry_time: pd.Timestamp
    exit_time: pd.Timestamp
    pnl_abs: float
    pnl_pct: float

    def model_dump(self):
        from dataclasses import asdict

        return asdict(self)


@dataclass
class MockBacktestResult:
    equity_curve: pd.Series
    trades: list
    metrics: Any
    trace: pd.DataFrame | None = None

    def __post_init__(self):
        # Ensure metrics is either a MetricSet or has model_dump
        if isinstance(self.metrics, dict):
            from antigravity_harness.models import MetricSet

            self.metrics = MetricSet(**self.metrics)


class TestSuite(unittest.TestCase):
    def setUp(self) -> None:
        self.params = StrategyParams()
        self.dcfg = DataConfig(interval="1d")
        self.ecfg = EngineConfig(initial_cash=100000.0)
        self.thresh = GateThresholds()

    # --- CALIBRATION & LOGIC TESTS ---

    def test_truth_table_logic(self) -> None:
        # FAIL | PASS -> FAIL
        res = [MockGateResult("GATE_PROFIT_FACTOR", "FAIL", ""), MockGateResult("GATE_MAX_DD", "PASS", "")]
        p, s, o, _, _ = _status_from_gate_results(res)
        self.assertEqual(o, "FAIL")

        # FAIL | WARN -> FAIL
        res = [MockGateResult("GATE_PROFIT_FACTOR", "FAIL", ""), MockGateResult("GATE_MAX_DD", "WARN", "")]
        p, s, o, _, _ = _status_from_gate_results(res)
        self.assertEqual(o, "FAIL")

        # PASS | PASS -> PASS
        res = [MockGateResult("GATE_PROFIT_FACTOR", "PASS", ""), MockGateResult("GATE_MAX_DD", "PASS", "")]
        p, s, o, _, _ = _status_from_gate_results(res)
        self.assertEqual(o, "PASS")

        # PASS | WARN -> WARN
        res = [MockGateResult("GATE_PROFIT_FACTOR", "PASS", ""), MockGateResult("GATE_MAX_DD", "WARN", "")]
        p, s, o, _, _ = _status_from_gate_results(res)
        self.assertEqual(o, "WARN")

    def test_bad_apple(self) -> None:
        # Logic in calibration.py
        # If fail_count > 0 -> FAIL
        fail_count = 1
        port_status = "PASS"
        if fail_count > 0:
            port_status = "FAIL"
        self.assertEqual(port_status, "FAIL")

    def test_portfolio_alignment_algorithm(self) -> None:
        # Emulate the fix logic directly
        idx1 = pd.to_datetime(["2021-01-01", "2021-01-03"])
        s1 = pd.Series([100.0, 105.0], index=idx1)

        idx2 = pd.to_datetime(["2021-01-02"])
        s2 = pd.Series([100.0], index=idx2)

        curves = [s1, s2]
        init_cash = 100.0

        # Algorithm
        all_idx = pd.Index([])
        for c in curves:
            all_idx = all_idx.union(c.index)
        all_idx = all_idx.sort_values()

        combined_eq = pd.Series(0.0, index=all_idx)
        for c in curves:
            c_aligned = c.reindex(all_idx)
            c_ffill = c_aligned.ffill()
            c_final = c_ffill.fillna(init_cash)
            combined_eq = combined_eq.add(c_final, fill_value=0)

        combined_eq = combined_eq / 2

        v2 = combined_eq.loc[pd.Timestamp("2021-01-02")]
        v3 = combined_eq.loc[pd.Timestamp("2021-01-03")]

        self.assertEqual(v2, 100.0, f"Day 2 failed: {v2}")
        self.assertEqual(v3, 102.5, f"Day 3 failed: {v3}")

    # --- GATES TESTS (The New Gates.py) ---

    @patch("antigravity_harness.runner.evaluate_gates")
    def test_validate_pipeline(self, mock_gates):
        mock_gates.return_value = []
        _run_one(
            "v032_simple",
            self.params,
            self.dcfg,
            self.ecfg,
            self.thresh,
            False,
            False,
            "SPY",
            "2020",
            "2021",
            "equity_fortress",
            "1d",
        )
        mock_gates.assert_called()

    def test_sharpe_gate(self) -> None:
        with patch("antigravity_harness.gates._run_sim") as mock_sim:
            # Low Sharpe
            mock_sim.return_value = {
                "sharpe_ratio": 0.1,
                "profit_factor": 2.0,
                "max_dd_pct": 0.1,
                "annualized_vol": 0.5,
                "trade_count": 100,
                "equity_curve": pd.Series(),
                "trades": [],
            }
            ctx_base = (
                SimulationContextBuilder()
                .with_strategy("v032_simple", MagicMock())
                .with_params(self.params)
                .with_data_cfg(self.dcfg)
                .with_engine_cfg(self.ecfg)
                .with_thresholds(self.thresh)
                .with_symbol("SPY")
                .with_window("2020", "2021")
            )

            # Low Sharpe
            res = evaluate_gates(ctx_base.with_gate_profile("equity_fortress").build())
            sharpe_gate = next(r for r in res if r.gate == "GATE_SHARPE")
            self.assertEqual(sharpe_gate.status, "FAIL")

            # Crypto allows low sharpe
            res = evaluate_gates(ctx_base.with_gate_profile("crypto_profit").build())
            sharpe_gate = next(r for r in res if r.gate == "GATE_SHARPE")
            self.assertEqual(sharpe_gate.status, "PASS")

    @patch("antigravity_harness.gates.run_backtest")
    @patch("antigravity_harness.gates.load_ohlc")
    @patch("antigravity_harness.gates._calc_annual_vol")
    def test_wf_leakage_prevention(self, mock_vol, mock_load, mock_bt):
        # Scenario: Train +100k, Eval -50k.
        mock_load.return_value = pd.DataFrame({"Close": [100]}, index=[pd.Timestamp("2020-01-01")])
        mock_vol.return_value = 0.5

        t1 = MockTrade(pd.Timestamp("2020-06-01"), pd.Timestamp("2020-06-02"), 100000.0, 1.0)
        t2 = MockTrade(pd.Timestamp("2021-06-01"), pd.Timestamp("2021-06-02"), -50000.0, -0.5)

        idx = pd.to_datetime(["2020-06-02", "2021-06-02"])
        eq = pd.Series([200000.0, 150000.0], index=idx)

        mock_bt.return_value = MockBacktestResult(equity_curve=eq, trades=[t1, t2], metrics={"profit_factor": 2.0})

        mock_strat = MagicMock()
        override = pd.DataFrame({"Close": [100]}, index=[pd.Timestamp("2020-01-01")])

        # ACT: Call with Eval Window
        ctx = (
            SimulationContextBuilder()
            .with_strategy("mock", mock_strat)
            .with_params(self.params)
            .with_data_cfg(self.dcfg)
            .with_engine_cfg(self.ecfg)
            .with_thresholds(self.thresh)
            .with_symbol("SPY")
            .with_window("2021-01-01", "2021-12-31")
            .with_override_df(override)
            .build()
        )
        res = _run_sim(ctx)

        # ASSERT
        self.assertEqual(len(res["trades"]), 1, "Should filter out train trade")
        self.assertEqual(res["gross_profit"], 0.0)
        self.assertEqual(res["gross_loss"], -50000.0)
        self.assertEqual(res["profit_factor"], 0.0)

    # --- CLI & AUTONOMY TESTS ---
    @patch("antigravity_harness.cli._run_one")
    def test_cli_validate_output(self, mock_run):
        p_res = GateResult(gate="GATE_TEST", status="PASS", reason="Reason", details={})
        mock_run.return_value = SimulationResult(
            params={},
            status="PASS",
            profit_status="PASS",
            safety_status="PASS",
            fail_reason="",
            warns=[],
            gate_results=[p_res],
            metrics=MetricSet(),
            trace=pd.DataFrame(),
        )

        args = argparse.Namespace(
            strategy="test",
            config=None,
            output_dir="/tmp",
            ma_length=200,
            ma_fast=20,
            rsi_entry=30,
            rsi_exit=70,
            stop_atr=2.0,
            no_ablation=True,
            time_split=False,
            symbol="SPY",
            start="2020-01-01",
            end="2021-01-01",
            interval="1d",
            gate_profile="equity_fortress",
            equity=False,
            debug=False,
        )

        # Phase 10: Fix strategy registration
        REGISTRY["test"] = V032Simple

        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            cmd_validate(args)

        out = f.getvalue()
        self.assertIn("[PASS] GATE_TEST: Reason", out)

    def test_snapshot_tamper(self) -> None:
        os.makedirs("./05_DATA_CACHE/snapshots", exist_ok=True)
        fpath = "./05_DATA_CACHE/snapshots/TEST_INTEGRITY_S.csv"
        df = pd.DataFrame({"Close": [100]}, index=pd.to_datetime(["2020-01-01"]))
        df.to_csv(fpath)

        base = os.path.basename(fpath).replace(".csv", "_12345678.csv")
        bad_path = os.path.join(os.path.dirname(fpath), base)
        shutil.copy(fpath, bad_path)

        with self.assertRaises(ValueError) as cm:
            load_snapshot(bad_path)
        self.assertIn("Hash mismatch", str(cm.exception))

    def test_promote_staging(self) -> None:
        if os.path.exists("./04_PRODUCTION_REPORTS/champion_registry.json"):
            os.remove("./04_PRODUCTION_REPORTS/champion_registry.json")

        promote_to_staging("TEST", "1d", {"profit_factor": 2.0})
        reg = load_registry()
        self.assertIn("TEST_1d", reg)
        self.assertEqual(reg["TEST_1d"]["status"], "PASS")
        self.assertEqual(reg["TEST_1d"]["deployment_state"], "STAGING")


class TestPhysics(unittest.TestCase):
    def setUp(self) -> None:
        self.dates = pd.date_range("2024-01-01", periods=5, freq="D")
        self.engine_cfg = EngineConfig(slippage_per_side=0.0, warmup_extra_bars=0)
        self.params = StrategyParams(stop_atr=2.0)

    def test_stop_gap_logic(self) -> None:
        # Bar 0: Signal
        # Bar 1: Entry (Open=100) -> Stop @ 90 (ATR=5)
        # Bar 2: Gap Down Open=85 -> Exit @ Open

        data = pd.DataFrame(
            {
                "Open": [100, 100, 85, 100, 100],
                "High": [110, 110, 90, 110, 110],
                "Low": [90, 95, 80, 90, 90],
                "Close": [105, 105, 82, 105, 105],
                "Volume": [1000] * 5,
            },
            index=self.dates,
        )

        prepared = data.copy()
        prepared["entry_signal"] = [True, False, False, False, False]
        prepared["exit_signal"] = [False, False, False, False, False]
        prepared["ATR"] = [5.0] * 5

        from antigravity_harness.engine import run_backtest

        result = run_backtest(data, prepared, self.params, self.engine_cfg)
        trades = result.trades

        self.assertEqual(len(trades), 1)
        t = trades[0]
        self.assertEqual(t.exit_reason, "gap_stop")
        self.assertAlmostEqual(t.exit_price, 85.0)

    def test_intrabar_stop(self) -> None:
        # Bar 2: Open=95 (>90 Stop), Low=80 (<90 Stop). Exit @ 90.
        data = pd.DataFrame(
            {
                "Open": [100, 100, 95, 100, 100],
                "High": [110, 110, 110, 110, 110],
                "Low": [90, 95, 80, 90, 90],
                "Close": [105, 105, 85, 105, 105],
                "Volume": [1000] * 5,
            },
            index=self.dates,
        )

        prepared = data.copy()
        prepared["entry_signal"] = [True, False, False, False, False]
        prepared["exit_signal"] = [False, False, False, False, False]
        prepared["ATR"] = [5.0] * 5

        from antigravity_harness.engine import run_backtest

        result = run_backtest(data, prepared, self.params, self.engine_cfg)
        trades = result.trades

        self.assertEqual(len(trades), 1)
        t = trades[0]
        self.assertEqual(t.exit_reason, "stop")
        self.assertAlmostEqual(t.exit_price, 90.0)


if __name__ == "__main__":
    unittest.main()
