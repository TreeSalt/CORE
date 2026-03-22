import unittest

import numpy as np
import pandas as pd

from mantis_core.engine import EngineConfig, StrategyParams, run_backtest


class TestEngine(unittest.TestCase):
    def setUp(self) -> None:
        # Create dummy OHLC data
        dates = pd.date_range("2024-01-01", periods=100, freq="1h")
        self.df = pd.DataFrame(
            {
                "Open": np.linspace(100, 200, 100),
                "High": np.linspace(101, 201, 100),
                "Low": np.linspace(99, 199, 100),
                "Close": np.linspace(100, 200, 100),
                "Volume": 1000,
            },
            index=dates,
        )

        self.params = StrategyParams()
        self.config = EngineConfig(initial_cash=10000.0)

    def test_run_backtest_basic(self) -> None:
        # Create dummy signals
        prepared = self.df.copy()
        prepared["entry_signal"] = False
        prepared["exit_signal"] = False
        prepared["ATR"] = 1.0

        # Trigger buy at bar 10
        prepared.iloc[10, prepared.columns.get_loc("entry_signal")] = True
        # Trigger exit at bar 20
        prepared.iloc[20, prepared.columns.get_loc("exit_signal")] = True

        res = run_backtest(self.df, prepared, self.params, self.config)

        self.assertIsNotNone(res.equity_curve)
        self.assertTrue(len(res.trades) > 0)
        self.assertEqual(res.trades[0].entry_time, self.df.index[11])  # Execution at i+1

    def test_run_backtest_alignment(self) -> None:
        # Test index alignment optimization
        prepared = self.df.copy()
        prepared["entry_signal"] = False
        prepared["exit_signal"] = False
        prepared["ATR"] = 1.0

        # Misalign index to force reindexing path
        prepared_shifted = prepared.shift(1).dropna()

        # Should handle it gracefully (though logic might be weird, it shouldn't crash)
        res = run_backtest(self.df, prepared_shifted, self.params, self.config)
        self.assertIsNotNone(res)


if __name__ == "__main__":
    unittest.main()
