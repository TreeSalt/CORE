import unittest

import numpy as np
import pandas as pd

from antigravity_harness.correlation import CorrelationGuard


class TestCorrelationGuard(unittest.TestCase):
    def test_filter_no_correlation(self):
        # A and B uncorrelated
        data = {
            "A": [1, 2, 3, 4, 3, 2, 1, 2, 3, 4],  # Periodic
            "B": [10, 10, 10, 10, 10, 10, 10, 10, 10, 9],  # Flatish
        }
        df = pd.DataFrame(data).pct_change().dropna()
        # They are not correlated
        kept = CorrelationGuard.filter(df, threshold=0.9)
        self.assertEqual(set(kept), {"A", "B"})

    def test_filter_high_correlation_pruning(self):
        # A and B highly correlated.
        # A = [1, 2, 3...]
        # B = [1.01, 2.01, 3.01...] almost same.
        # But let's make B more volatile.
        base = np.array([100, 101, 102, 101, 100, 99, 98, 99, 100, 101])

        # A is base
        # B is base * 2 (Same direction, higher amplitude => Same Correlation, Higher Vol)

        df = pd.DataFrame({"A": base, "B": base * 2})
        rets = df.pct_change().dropna()

        # Corr should be 1.0
        corr = rets.corr().iloc[0, 1]
        self.assertGreater(corr, 0.99)

        # Vols
        vols = rets.std()
        # B vol should be ... actually wait.
        # pct_change of (X * 2) is same as pct_change of X?
        # (2*X2 - 2*X1) / 2*X1 = 2(X2-X1) / 2*X1 = (X2-X1)/X1.
        # YES. Scaling returns doesn't change pct_change distribution if scale is constant.
        # The volatility of RETURNS is identical if price is just scaled.

        # We need B to have wider swings.
        # Let's add noise to B that correlates but is wilder.
        np.random.seed(42)
        base_rets = np.random.normal(0, 0.01, 100)

        # A = base
        # B = base + small noise? No that reduces correlation.
        # B = base * 1.5? (Levered)
        # Returns of B = 1.5 * Returns of A?
        # Yes. If PriceB = PriceA with leverage?
        # If P_b = P_a * 1.5, returns are same.
        # If Ret_B = Ret_A * 1.5.

        df_rets = pd.DataFrame(
            {
                "A": base_rets,
                "B": base_rets * 1.5,  # 1.5x beta
            }
        )

        # Corr check
        corr = df_rets.corr().iloc[0, 1]
        self.assertGreater(corr, 0.99)

        # Vol check
        vols = df_rets.std()
        self.assertGreater(vols["B"], vols["A"])

        # Filter
        kept = CorrelationGuard.filter(df_rets, threshold=0.9)

        # B should be dropped (High Vol)
        self.assertIn("A", kept)
        self.assertNotIn("B", kept)
        self.assertEqual(len(kept), 1)

    def test_filter_chain(self):
        # A, B, C.
        # A-B Corr. B-C Corr. A-C Uncorr.
        # A low vol. B medium vol. C high vol.
        # A-B conflict -> B dropped (medium > low).
        # B-C conflict? B is gone. C stays?
        # Or does B prune C first?
        # The logic iterates upper triangle.
        # (A, B) -> Drop B.
        # (A, C) -> Keep.
        # (B, C) -> Loop continues. B is already in to_drop. "if asset_a in to_drop... continue".
        # So B cannot prune C if B is already dead.
        # Result: Keep A, Keep C.

        pass
