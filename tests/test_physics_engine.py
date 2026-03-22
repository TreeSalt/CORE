import unittest
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd

from mantis_core.config import DataConfig, EngineConfig, GateThresholds, StrategyParams
from mantis_core.context import SimulationContextBuilder
from mantis_core.gates import _run_sim
from mantis_core.metrics import compute_metrics
from mantis_core.strategies.base import Strategy
from mantis_core.utils import infer_periods_per_year


class TestPhysicsEngine(unittest.TestCase):
    def test_infer_periods_per_year(self):
        # Crypto (365 days)
        self.assertEqual(infer_periods_per_year("1d", is_crypto=True), 365)
        self.assertEqual(infer_periods_per_year("4h", is_crypto=True), 2190)
        self.assertEqual(infer_periods_per_year("1h", is_crypto=True), 8760)

        # Equity (252 days)
        # 1d = 252
        self.assertEqual(infer_periods_per_year("1d", is_crypto=False), 252)
        # 4h = 410 (390 mins/day / 240 mins/bar = 1.625 bars/day * 252 = 409.5 -> 410)
        self.assertEqual(infer_periods_per_year("4h", is_crypto=False), 410)

    def test_compute_metrics_physics(self):
        # Create a dummy equity curve with known returns
        # 1% daily return, flat.
        equity = [100 * (1.01) ** i for i in range(100)]
        equity_s = pd.Series(equity)
        trades = []

        # Case 1: 1d (365)
        # Sharpe should be roughly sqrt(365) * mean/std
        # constant return -> std is near 0 -> sharpe huge.

        # Let's use alternating returns to get measurable std
        # +1%, -1%, +1%, -1%...
        eq_vals = [100.0]
        for i in range(100):
            ret = 0.01 if i % 2 == 0 else -0.01
            eq_vals.append(eq_vals[-1] * (1 + ret))

        dates = pd.date_range("2020-01-01", periods=101, freq="D")
        equity_s = pd.Series(eq_vals, index=dates)

        m_365 = compute_metrics(equity_s, trades, periods_per_year=365)
        m_2190 = compute_metrics(equity_s, trades, periods_per_year=2190)

        # Sharpe ~ sqrt(periods)
        # sharpe_2190 / sharpe_365 should be sqrt(2190)/sqrt(365) = sqrt(6) ~= 2.45
        ratio = m_2190["daily_sharpe"] / m_365["daily_sharpe"]
        self.assertAlmostEqual(ratio, np.sqrt(6), delta=0.1)

    @patch("mantis_core.gates.run_backtest")
    def test_gates_injection(self, mock_run_backtest):
        # Setup mocks
        mock_strat = MagicMock(spec=Strategy)
        mock_strat.prepare_data.return_value = pd.DataFrame()

        data_cfg = DataConfig(interval="4h")  # Should infer 2190 (Crypto default)
        engine_cfg = EngineConfig(is_crypto=True)
        params = StrategyParams()

        # Create dummy DF with enough length
        dates = pd.date_range("2020-01-01", periods=100, freq="4h")
        df = pd.DataFrame({"Open": 100, "High": 100, "Low": 100, "Close": 100, "Volume": 1000}, index=dates)

        # Mock result
        from mantis_core.models import MetricSet

        mock_res = MagicMock()
        mock_res.metrics = MetricSet()
        mock_res.equity_curve = pd.Series(dtype=float)
        mock_res.trades = []
        mock_res.trace = None
        mock_run_backtest.return_value = mock_res

        # Run
        ctx = (
            SimulationContextBuilder()
            .with_strategy("mock", mock_strat)
            .with_params(params)
            .with_data_cfg(data_cfg)
            .with_engine_cfg(engine_cfg)
            .with_thresholds(GateThresholds())
            .with_symbol("BTC")
            .with_window("2020-01-01", "2020-01-02")
            .with_override_df(df)
            .build()
        )
        _run_sim(ctx)

        # Verify engine_cfg passed to run_backtest has periods_per_year=2190
        args, _ = mock_run_backtest.call_args
        passed_cfg = args[3]
        self.assertEqual(passed_cfg.periods_per_year, 2190)


if __name__ == "__main__":
    unittest.main()
