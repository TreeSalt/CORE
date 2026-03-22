import unittest

import pandas as pd

from mantis_core.regimes import RegimeConfig, RegimeFlag, RegimeLabel, detect_regime


class TestRegimeSpec(unittest.TestCase):
    def setUp(self):
        self.cfg = RegimeConfig(
            window=24, trend_threshold=0.5, vol_ratio_threshold=1.2, panic_drawdown=-0.15, panic_vol_spike=2.0
        )
        # Synthetic data: 3 assets, 100 days
        dates = pd.date_range("2021-01-01", periods=100, freq="D")
        self.dates = dates

        # Base scenario: Flat then Trend
        self.prices = pd.DataFrame(index=dates)
        self.prices["A"] = 100.0
        self.prices["B"] = 50.0
        self.prices["C"] = 10.0

        # Create a trend from day 50
        for i in range(50, 100):
            self.prices.iloc[i] = self.prices.iloc[i - 1] * 1.01  # 1% daily trend

    def test_scale_invariance(self):
        """
        Physics Law: Multiply any asset by Constant K -> Regime Label MUST NOT CHANGE.
        """
        # 1. Baseline detection at t=90
        asof = self.dates[90]
        base_state = detect_regime(self.prices, asof, self.cfg)

        # 2. Scramble scales
        scaled_prices = self.prices.copy()
        scaled_prices["A"] *= 100.0  # A is now 10,000+
        scaled_prices["B"] *= 0.001  # B is now penny stock
        # C stays same

        scaled_state = detect_regime(scaled_prices, asof, self.cfg)

        # Assertions
        self.assertEqual(base_state.label, scaled_state.label, "Regime Label changed after scaling!")
        self.assertAlmostEqual(
            base_state.metrics["trend_z"],
            scaled_state.metrics["trend_z"],
            places=5,
            msg="trend_z changed after scaling",
        )
        self.assertAlmostEqual(
            base_state.metrics["vol_ratio"],
            scaled_state.metrics["vol_ratio"],
            places=5,
            msg="vol_ratio changed after scaling",
        )
        self.assertAlmostEqual(
            base_state.metrics["drawdown"],
            scaled_state.metrics["drawdown"],
            places=5,
            msg="drawdown changed after scaling",
        )

    def test_trend_z_dimensionless(self):
        """
        Trend Z must be roughly invariant to volatility magnitude if Sharpe-like.
        If we double returns magnitude (2x lev), does Trend Z stay same?
        Strictly speaking: Mean/Std -> (2*Mean)/(2*Std) = Same.
        """
        asof = self.dates[90]
        base_state = detect_regime(self.prices, asof, self.cfg)

        # Create 2x leveraged prices (approx)
        # returns = pct_change
        lev_prices = self.prices.copy()
        # Reconstruct from 2x returns
        rets = self.prices.pct_change().fillna(0) * 2.0
        lev_prices = (1 + rets).cumprod() * 100.0

        lev_state = detect_regime(lev_prices, asof, self.cfg)

        # Should be identical because (2x mean) / (2x std) = 1x ratio
        self.assertAlmostEqual(base_state.metrics["trend_z"], lev_state.metrics["trend_z"], places=4)

    def test_panic_monotonicity(self):
        """
        If we trigger panic conditions, it must be PANIC.
        """
        # Force a crash scenario
        crash_prices = self.prices.copy()
        # Induce -30% drop over last 5 days
        # end_idx = 80
        for i in range(75, 81):
            crash_prices.iloc[i] = crash_prices.iloc[i - 1] * 0.90  # -10% per day

        asof = self.dates[80]
        # This guarantees DD < -0.15 and likely high vol

        state = detect_regime(crash_prices, asof, self.cfg)

        # Verify metrics
        self.assertLess(state.metrics["drawdown"], -0.15)
        self.assertTrue(RegimeFlag.PANIC in state.flags or state.label == RegimeLabel.PANIC)
        self.assertEqual(state.label, RegimeLabel.PANIC)

    def test_lookahead_safety(self):
        """
        Decision at T must NOT see T+1 data.
        """
        t_idx = 50
        asof = self.dates[t_idx]

        # Run on normal data
        state_1 = detect_regime(self.prices, asof, self.cfg)

        # Modify future data (t+1) massively
        future_mod = self.prices.copy()
        future_mod.iloc[t_idx + 1 :] = future_mod.iloc[t_idx + 1 :] * 0.0  # Crash to zero tomorrow

        state_2 = detect_regime(future_mod, asof, self.cfg)

        self.assertEqual(state_1.label, state_2.label, "Future data leaked into current decision!")
        self.assertEqual(state_1.metrics["trend_z"], state_2.metrics["trend_z"])


if __name__ == "__main__":
    unittest.main()
