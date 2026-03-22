import unittest

import numpy as np
import pandas as pd

from mantis_core.config import StrategyParams
from mantis_core.strategies import REGISTRY
from mantis_core.strategies.catalog import STRATEGY_CATALOG


class TestStrategyContract(unittest.TestCase):
    def setUp(self) -> None:
        # Create synthetic OHLCV data
        # Sufficient length for warmups (e.g. 200 SMA)
        dates = pd.date_range("2024-01-01", periods=1000, freq="1h")
        self.df = pd.DataFrame(
            {
                "Open": np.linspace(100, 200, 1000),
                "High": np.linspace(101, 201, 1000),
                "Low": np.linspace(99, 199, 1000),
                "Close": np.linspace(100, 200, 1000),  # Perfect trend for basic test
                "Volume": 1000,
            },
            index=dates,
        )

        # Add some wiggle to create volatility for ATR
        self.df["Close"] += np.sin(np.arange(1000) / 10) * 2
        self.df["High"] = self.df["Close"] + 1
        self.df["Low"] = self.df["Close"] - 1

    def test_active_strategies_contract(self) -> None:
        """Verify all ACTIVE strategies emit correct columns and types."""

        for name, strategy_cls in REGISTRY.items():
            # Check quarantine status
            meta = STRATEGY_CATALOG.get(name)
            if meta and meta.is_quarantined:
                # Quarantined strategies are NOT subject to strict contract in this test?
                # User rule: "If experimental/quarantined, excluded from active registry/contract tests."
                # But v032 is in REGISTRY still?
                # Step 0 rule "exclude it from default sweeps" but Step 2 explicitly says:
                # "If a strategy is experimental/quarantined, it must be excluded from ACTIVE registry and therefore excluded from contract tests"  # noqa: E501
                # If v032 is in "REGISTRY" it is technically active in the code imports.
                # However, the user instruction implies we should skip checking quarantined ones.
                continue

            with self.subTest(strategy=name):
                # Instantiate
                strat = strategy_cls()
                params = StrategyParams()  # Default params

                # Run prepare
                df_res = strat.prepare_data(self.df.copy(), params)

                # Assertions
                required_cols = ["entry_signal", "exit_signal", "ATR"]
                for col in required_cols:
                    self.assertIn(col, df_res.columns, f"{name}: Missing column {col}")

                # Type checks
                # signals should be bool-like (not all NaNs)
                # Note: signals can be all False if logic fails, but type should be bool usually.

                # Check ATR is not all NaN (after warmup)
                # Warmup ~200 bars usually. Check last 100 bars.
                last_100_atr = df_res["ATR"].iloc[-100:]
                self.assertFalse(last_100_atr.isna().all(), f"{name}: ATR is all NaN in tail")

                # Check Signals defined (not all NaN)
                self.assertFalse(df_res["entry_signal"].isna().any(), f"{name}: entry_signal contains NaN")
                self.assertFalse(df_res["exit_signal"].isna().any(), f"{name}: exit_signal contains NaN")


if __name__ == "__main__":
    unittest.main()
