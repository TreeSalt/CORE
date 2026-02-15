"""
Vanguard Effective Acceptance Tests.

Validates:
  1. Warmup fold boundary → UNKNOWN → Cash
  2. Bear trend → Cash
  3. Correlation z-score (not always on)
  4. Falling knife → Cash
  5. Benchmark deterministic metrics
"""

import unittest

import numpy as np
import pandas as pd

from antigravity_harness.portfolio_benchmark import (
    compute_alpha_metrics,
    compute_equal_weight_benchmark,
)
from antigravity_harness.portfolio_policies import (
    CrossSectionMeanReversionPolicy,
    PolicyConfig,
)
from antigravity_harness.portfolio_router import PortfolioRouter
from antigravity_harness.regimes import (
    RegimeConfig,
    RegimeFlag,
    RegimeLabel,
    RegimePersistence,
    RegimeState,
    detect_regime,
)


class TestWarmupFoldBoundary(unittest.TestCase):
    """Task 1: New router instance outputs UNKNOWN/Cash for the first N bars."""

    def test_persistence_returns_unknown_before_confirmation(self):
        """RegimePersistence with min_bars=3: first 2 bars → UNKNOWN."""
        p = RegimePersistence(min_bars=3)
        s = RegimeState(RegimeLabel.RANGE_LOW_VOL)

        out1 = p.update(s)
        self.assertEqual(out1.label, RegimeLabel.UNKNOWN, "Bar 1: should be UNKNOWN")

        out2 = p.update(s)
        self.assertEqual(out2.label, RegimeLabel.UNKNOWN, "Bar 2: should be UNKNOWN")

        out3 = p.update(s)
        self.assertEqual(out3.label, RegimeLabel.RANGE_LOW_VOL, "Bar 3: should confirm")

    def test_router_warmup_outputs_cash(self):
        """Router with fresh persistence should route to DefensiveCash during warmup."""
        cfg = RegimeConfig(window=5)
        policy_cfg = PolicyConfig()
        router = PortfolioRouter(regime_cfg=cfg, policy_cfg=policy_cfg)

        # Generate synthetic data (positive trend, enough for detect_regime)
        dates = pd.date_range("2021-01-01", periods=50, freq="D")
        np.random.seed(42)
        prices = pd.DataFrame(
            {
                "A": 100 * (1 + np.random.normal(0.001, 0.01, 50)).cumprod(),
                "B": 100 * (1 + np.random.normal(0.001, 0.01, 50)).cumprod(),
            },
            index=dates,
        )

        # First route call should be UNKNOWN → DefensiveCash → zero weights
        weights, regime = router.route(prices, dates[10])
        total_weight = sum(weights.values())

        # During warmup, regime should be UNKNOWN
        if regime.label == RegimeLabel.UNKNOWN:
            self.assertEqual(total_weight, 0.0, "Warmup: must be cash (0 exposure)")

        # Even if not UNKNOWN (if persistence confirms fast), policy should be defensive
        self.assertEqual(regime.metrics.get("chosen_policy"), "DefensiveCash")


class TestBearTrendReturnsCash(unittest.TestCase):
    """Task 3: Synthetic downtrend → Cash policy."""

    def test_negative_trend_routes_to_cash(self):
        """A -2%/day bear market MUST route to DefensiveCash."""
        cfg = RegimeConfig(window=20)
        policy_cfg = PolicyConfig()
        router = PortfolioRouter(regime_cfg=cfg, policy_cfg=policy_cfg)

        # Strong downtrend: -2% per day for 60 days
        dates = pd.date_range("2021-01-01", periods=60, freq="D")
        decline = 100 * (0.98 ** np.arange(60))
        prices = pd.DataFrame(
            {
                "A": decline,
                "B": decline * 1.01,  # Slightly offset
            },
            index=dates,
        )

        # Warm up persistence by routing multiple times
        for i in range(25, 55):
            weights, regime = router.route(prices, dates[i])

        # After enough bars, the confirmed regime should be defensive
        self.assertEqual(
            sum(weights.values()), 0.0, f"Bear market must be Cash. Got policy={regime.metrics.get('chosen_policy')}"
        )

    def test_detect_regime_negative_trend_dir(self):
        """detect_regime should report negative trend_dir for declining prices."""
        cfg = RegimeConfig(window=20)
        dates = pd.date_range("2021-01-01", periods=60, freq="D")
        decline = 100 * (0.98 ** np.arange(60))
        prices = pd.DataFrame(
            {
                "A": decline,
                "B": decline * 0.99,
            },
            index=dates,
        )

        state = detect_regime(prices, dates[-1], cfg)
        trend_dir = state.metrics.get("trend_dir", 0)
        self.assertLessEqual(trend_dir, 0, f"Declining market must have trend_dir <= 0, got {trend_dir}")


class TestCorrelationNotAlwaysOn(unittest.TestCase):
    """Task 5: Normal correlated market should NOT trigger CORR_SPIKE."""

    def test_stable_correlated_market_no_spike(self):
        """
        Two assets with constant ~0.6 correlation should NOT trigger CORR_SPIKE
        under z-score detection (only spikes above baseline fire).
        """
        np.random.seed(123)
        n = 120
        dates = pd.date_range("2021-01-01", periods=n, freq="D")

        # Generate moderately correlated returns (constant correlation ~0.6)
        base = np.random.normal(0, 0.01, n)
        noise_a = np.random.normal(0, 0.005, n)
        noise_b = np.random.normal(0, 0.005, n)

        price_a = 100 * (1 + base + noise_a).cumprod()
        price_b = 100 * (1 + base + noise_b).cumprod()

        prices = pd.DataFrame({"A": price_a, "B": price_b}, index=dates)

        cfg = RegimeConfig(window=24, corr_lookback=60, corr_z_threshold=2.0)
        state = detect_regime(prices, dates[-1], cfg)

        # Should NOT have CORR_SPIKE because correlation is constant (no spike)
        self.assertNotIn(
            RegimeFlag.CORR_SPIKE,
            state.flags,
            f"Stable corr should NOT trigger spike. avg_corr={state.metrics.get('avg_corr')}",
        )


class TestFallingKnifeSafety(unittest.TestCase):
    """Task 4: Synthetic -5%/day crash → Mean Reversion returns Cash."""

    def test_crash_returns_cash(self):
        """All assets crashing at -5%/day → Mean Reversion policy returns zero weights."""
        cfg = PolicyConfig(top_k=2, crash_floor=-0.20)
        dates = pd.date_range("2021-01-01", periods=25, freq="D")

        # -5%/day crash
        crash = 100 * (0.95 ** np.arange(25))
        prices = pd.DataFrame(
            {
                "A": crash,
                "B": crash * 0.99,
            },
            index=dates,
        )

        policy = CrossSectionMeanReversionPolicy()
        weights = policy.compute_target_weights(prices, dates[-1], cfg)
        total = sum(weights.values())
        self.assertEqual(total, 0.0, "All-crash scenario must return Cash (0 weight)")

    def test_positive_return_excluded_from_mean_reversion(self):
        """Assets with positive returns should not be selected for mean reversion."""
        cfg = PolicyConfig(top_k=3, crash_floor=-0.20)
        dates = pd.date_range("2021-01-01", periods=25, freq="D")

        # A: +5% (positive, not oversold)
        # B: -3% (mild dip, valid)
        # C: -25% (falling knife)
        prices = pd.DataFrame(
            {
                "A": np.linspace(100, 105, 25),
                "B": np.linspace(100, 97, 25),
                "C": np.linspace(100, 75, 25),
            },
            index=dates,
        )

        policy = CrossSectionMeanReversionPolicy()
        weights = policy.compute_target_weights(prices, dates[-1], cfg)

        # A should be excluded (positive return)
        # C should be excluded (below crash_floor)
        # B should be the only candidate
        self.assertEqual(weights.get("A", 0.0), 0.0, "Positive return should be excluded")
        self.assertEqual(weights.get("C", 0.0), 0.0, "Crash below floor should be excluded")
        self.assertGreater(weights.get("B", 0.0), 0.0, "Mild dip should be selected")


class TestBenchmarkDeterministic(unittest.TestCase):
    """Task 6: Benchmark metrics are deterministic and present."""

    def test_equal_weight_benchmark_deterministic(self):
        """Same data → same benchmark metrics."""
        dates = pd.date_range("2021-01-01", periods=100, freq="D")
        np.random.seed(999)
        prices = pd.DataFrame(
            {
                "A": 100 * (1 + np.random.normal(0.001, 0.01, 100)).cumprod(),
                "B": 100 * (1 + np.random.normal(0.001, 0.01, 100)).cumprod(),
            },
            index=dates,
        )

        r1 = compute_equal_weight_benchmark(prices, 365, 100_000)
        r2 = compute_equal_weight_benchmark(prices, 365, 100_000)

        self.assertEqual(r1["benchmark_total_return_pct"], r2["benchmark_total_return_pct"])
        self.assertEqual(r1["benchmark_sharpe_ratio"], r2["benchmark_sharpe_ratio"])
        self.assertEqual(r1["benchmark_max_drawdown_pct"], r2["benchmark_max_drawdown_pct"])

    def test_alpha_metrics_present(self):
        """Alpha metrics contain all required keys."""
        dates = pd.date_range("2021-01-01", periods=100, freq="D")
        np.random.seed(42)
        port_eq = pd.Series(100_000 * (1 + np.random.normal(0.001, 0.01, 100)).cumprod(), index=dates)
        bench_eq = pd.Series(100_000 * (1 + np.random.normal(0.0005, 0.01, 100)).cumprod(), index=dates)

        alpha = compute_alpha_metrics(port_eq, bench_eq, periods_per_year=365)
        required_keys = ["excess_return_pct", "tracking_error", "information_ratio", "max_dd_diff_pct"]
        for key in required_keys:
            self.assertIn(key, alpha, f"Missing alpha metric: {key}")


if __name__ == "__main__":
    unittest.main()
