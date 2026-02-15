import unittest

import numpy as np
import pandas as pd

from antigravity_harness.optimization import Optimizer


class TestOptimization(unittest.TestCase):
    def test_equal_weight(self):
        syms = ["A", "B", "C", "D"]
        w = Optimizer.equal_weight(syms)
        self.assertEqual(len(w), 4)
        for s in syms:
            self.assertEqual(w[s], 0.25)

    def test_inverse_volatility(self):
        # Create synthetic returns
        # A: Stable (Vol 0.01)
        # B: Volatile (Vol 0.02)
        # B is 2x more volatile -> Should have 1/2 the weight of A?
        # InvVol(A) = 1/0.01 = 100
        # InvVol(B) = 1/0.02 = 50
        # Total = 150.
        # W(A) = 100/150 = 0.666...
        # W(B) = 50/150 = 0.333...

        np.random.seed(42)
        # 100 days
        returns_a = np.random.normal(0, 0.01, 100)
        returns_b = np.random.normal(0, 0.02, 100)

        df = pd.DataFrame({"A": returns_a, "B": returns_b})

        # Verify std dev approx
        # std_a ~ 0.01, std_b ~ 0.02

        w = Optimizer.inverse_volatility(df, window=100)

        print(f"Weights: {w}")

        self.assertTrue(w["A"] > w["B"])
        self.assertAlmostEqual(w["A"] + w["B"], 1.0)

        # Check ratio approx 2:1
        # Allow some noise
        ratio = w["A"] / w["B"]
        self.assertTrue(1.5 < ratio < 2.5)  # noqa: PLR2004

    def test_zero_vol_handling(self):
        # If asset has 0 vol (flat line)
        df = pd.DataFrame({"A": [0.0] * 10, "B": [0.0] * 10})
        # Should fallback to equal weight
        w = Optimizer.inverse_volatility(df)
        self.assertEqual(w["A"], 0.5)
        self.assertEqual(w["B"], 0.5)
