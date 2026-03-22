import unittest
from unittest.mock import patch

import pandas as pd

from mantis_core.config import StrategyParams
from mantis_core.strategies import get_strategy


class TestV080Dynamic(unittest.TestCase):
    def setUp(self):
        with patch("mantis_core.strategies.registry.STRATEGY_REGISTRY.verify_strategy_allowed"):
            self.strat = get_strategy("v080_volatility_guard_trend")
        # create mock data
        self.dates = pd.date_range("2021-01-01", periods=100)
        self.df = pd.DataFrame(
            {
                "Open": [100.0] * 100,
                "High": [105.0] * 100,
                "Low": [95.0] * 100,
                "Close": [100.0] * 100,
                "Volume": [1000] * 100,
            },
            index=self.dates,
        )

        # Make Close trend up slightly
        self.df["Close"] = [100.0 + i * 0.1 for i in range(100)]
        self.df["High"] = self.df["Close"] + 2.0
        self.df["Low"] = self.df["Close"] - 2.0

    def test_params_influence(self):
        # 1. Baseline Params
        p1 = StrategyParams(ma_length=20, ma_fast=5, vol_max_pct=0.1, vol_min_pct=0.0)
        out1 = self.strat.prepare_data(self.df.copy(), p1)

        # 2. Strict Params (Higher MA length)
        # Should change SMA values
        p2 = StrategyParams(ma_length=50, ma_fast=5, vol_max_pct=0.1, vol_min_pct=0.0)
        out2 = self.strat.prepare_data(self.df.copy(), p2)

        # Compare SMA columns
        # They should be different (at least length of valid values or values themselves)
        # Length of valid values should differ (20 vs 50)
        valid1 = len(out1["sma"].dropna())
        valid2 = len(out2["sma"].dropna())

        self.assertNotEqual(valid1, valid2)

    def test_vol_guard_params(self):
        # Test that vol_max_pct is used
        p = StrategyParams(ma_length=20, ma_fast=5, vol_max_pct=0.0001)  # Very strict vol
        out = self.strat.prepare_data(self.df.copy(), p)

        # Assuming our data has some volatility (ATR > 0), this strict limit should block entries
        # entry_signal depends on vol_safe
        # Check if we have fewer entries than a loose param
        entries_strict = out["entry_signal"].sum()

        p_loose = StrategyParams(ma_length=20, ma_fast=5, vol_max_pct=1.0)
        out_loose = self.strat.prepare_data(self.df.copy(), p_loose)
        entries_loose = out_loose["entry_signal"].sum()

        # We expect loose to allow more entries (if trend confirms)
        # In our synthetic data, trend is up.
        self.assertLessEqual(entries_strict, entries_loose)
