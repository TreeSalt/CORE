"""
Test: Scale-Invariant Basket Drawdown
Verify that multiplying one asset's prices by 10x does NOT change:
  1. Regime detection decisions (label, flags)
  2. Basket drawdown values
  3. Panic trigger behavior
"""

import unittest

import numpy as np
import pandas as pd

from antigravity_harness.regimes import RegimeConfig, detect_regime


class TestBasketScaleInvariance(unittest.TestCase):
    """Basket drawdown and regime decisions must be scale-invariant."""

    @staticmethod
    def _build_prices(scale_factor: float = 1.0) -> pd.DataFrame:
        """Build synthetic OHLCV close prices. One asset can be scaled."""
        np.random.seed(99)
        dates = pd.date_range("2021-01-01", periods=60, freq="D")
        base_a, base_b, base_c = 100.0, 50.0, 200.0

        def _walk(base, n=60):
            prices = [base]
            for _ in range(n - 1):
                ret = np.random.normal(-0.005, 0.03)  # slight downward bias for drawdown
                prices.append(prices[-1] * (1 + ret))
            return prices

        # Reset seed for each call to ensure identical random walks
        np.random.seed(99)
        prices_a = _walk(base_a)
        prices_b = _walk(base_b * scale_factor)  # scale asset B
        prices_c = _walk(base_c)

        return pd.DataFrame(
            {
                "A": prices_a,
                "B": prices_b,
                "C": prices_c,
            },
            index=dates,
        )

    def test_drawdown_scale_invariant(self):
        """Basket drawdown must be identical regardless of asset price scale."""
        cfg = RegimeConfig(window=24)
        asof = pd.Timestamp("2021-02-28")

        # Normal prices
        df_normal = self._build_prices(scale_factor=1.0)
        regime_normal = detect_regime(df_normal, asof, cfg)

        # Scale asset B by 10x
        df_scaled = self._build_prices(scale_factor=10.0)
        regime_scaled = detect_regime(df_scaled, asof, cfg)

        # Drawdown must be identical (returns-based, not price-based)
        self.assertAlmostEqual(
            regime_normal.metrics["drawdown"],
            regime_scaled.metrics["drawdown"],
            places=6,
            msg=f"Drawdown changed with 10x scaling: "
            f"{regime_normal.metrics['drawdown']:.6f} vs {regime_scaled.metrics['drawdown']:.6f}",
        )

    def test_regime_label_scale_invariant(self):
        """Regime label and flags must not change with price scaling."""
        cfg = RegimeConfig(window=24)
        asof = pd.Timestamp("2021-02-28")

        df_normal = self._build_prices(scale_factor=1.0)
        df_scaled = self._build_prices(scale_factor=10.0)

        r1 = detect_regime(df_normal, asof, cfg)
        r2 = detect_regime(df_scaled, asof, cfg)

        self.assertEqual(r1.label, r2.label, f"Regime label changed: {r1.label} → {r2.label}")
        self.assertEqual(r1.flags, r2.flags, f"Regime flags changed: {r1.flags} → {r2.flags}")

    def test_panic_trigger_scale_invariant(self):
        """Panic detection must be identical under price scaling."""
        # Use aggressive thresholds to potentially trigger panic
        cfg = RegimeConfig(window=24, panic_drawdown=-0.05, panic_vol_spike=1.0)
        asof = pd.Timestamp("2021-02-28")

        df_normal = self._build_prices(scale_factor=1.0)
        df_scaled = self._build_prices(scale_factor=100.0)  # 100x scaling

        r1 = detect_regime(df_normal, asof, cfg)
        r2 = detect_regime(df_scaled, asof, cfg)

        self.assertEqual(r1.label, r2.label, f"Panic trigger changed with 100x scaling: {r1.label} → {r2.label}")


if __name__ == "__main__":
    unittest.main()
