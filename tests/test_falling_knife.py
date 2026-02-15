"""
Test: Falling Knife Guard
Verify that Mean Reversion policy avoids assets with >20% drawdown in the lookback window.
"""

import unittest

import numpy as np
import pandas as pd

from antigravity_harness.portfolio_policies import CrossSectionMeanReversionPolicy, PolicyConfig


class TestFallingKnife(unittest.TestCase):
    def test_falling_knife_filter(self):
        # Create 3 assets:
        # A: -5% return (Good dip)
        # B: -25% return (Falling Knife)
        # C: +5% return (Ignore)

        cfg = PolicyConfig(top_k=2, lookback=10)
        dates = pd.date_range("2021-01-01", periods=11)

        # A: 100 -> 95
        # B: 100 -> 75
        # C: 100 -> 105

        prices = pd.DataFrame(
            {"A": np.linspace(100, 95, 11), "B": np.linspace(100, 75, 11), "C": np.linspace(100, 105, 11)}, index=dates
        )

        policy = CrossSectionMeanReversionPolicy()
        weights = policy.compute_target_weights(prices, dates[-1], cfg)

        # Expect B to be excluded despite being the "best" loser (lowest return)
        # A should be included

        self.assertIn("A", weights)
        # self.assertNotIn("B", weights) # Key might exist with 0.0
        self.assertGreater(weights["A"], 0.0)
        self.assertEqual(weights.get("B", 0.0), 0.0)

    def test_all_knives(self):
        # All assets crashed > 20%
        cfg = PolicyConfig(top_k=2)
        dates = pd.date_range("2021-01-01", periods=11)

        prices = pd.DataFrame({"A": np.linspace(100, 70, 11), "B": np.linspace(100, 75, 11)}, index=dates)

        policy = CrossSectionMeanReversionPolicy()
        weights = policy.compute_target_weights(prices, dates[-1], cfg)

        # Should return empty/zero weights
        total_weight = sum(weights.values())
        self.assertEqual(total_weight, 0.0)


if __name__ == "__main__":
    unittest.main()
