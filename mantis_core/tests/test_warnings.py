import unittest
import warnings

import pandas as pd

from mantis_core.config import EngineConfig, StrategyParams
from mantis_core.engine import run_backtest


class TestEngineWarnings(unittest.TestCase):
    def test_no_future_warnings_on_signals(self) -> None:
        """
        Regression test for Task A: Ensure zero FutureWarnings during signal extraction.
        Pandas often warns when fillna() is used on columns that might need downcasting (None -> False).
        """
        # 1. Setup mock OHLC data
        dates = pd.date_range("2024-01-01", periods=20, freq="D")
        data = pd.DataFrame(
            {
                "Open": 100.0,
                "High": 105.0,
                "Low": 95.0,
                "Close": 102.0,
                "Volume": 1000,
            },
            index=dates,
        )

        # 2. Setup mock signal dataframe with mixed types (bool and None) which triggers the warning
        # Using Object dtype forces the check
        sigs = pd.DataFrame(index=dates)
        sigs["entry_signal"] = [True, False, None, True, False, None] + [False] * 14
        sigs["exit_signal"] = [False, False, False, False, True, None] + [False] * 14
        sigs["ATR"] = 1.0  # Required column

        # Ensure it's object dtype to really probe the fillna behavior
        sigs["entry_signal"] = sigs["entry_signal"].astype(object)
        sigs["exit_signal"] = sigs["exit_signal"].astype(object)

        params = StrategyParams()
        cfg = EngineConfig()

        # 3. Catch warnings and fail if any FutureWarning exists
        with warnings.catch_warnings(record=True) as caught_warnings:
            warnings.simplefilter("always")  # Capture EVERYTHING

            # Execute engine
            run_backtest(data, sigs, params, cfg)

            # Filter specifically for FutureWarnings
            future_warns = [w for w in caught_warnings if issubclass(w.category, FutureWarning)]

            if future_warns:
                msg = "\n".join([f"{w.category.__name__}: {w.message}" for w in future_warns])
                self.fail(f"TASK A FAILURE: Detected {len(future_warns)} FutureWarnings during engine run:\n{msg}")


if __name__ == "__main__":
    unittest.main()
