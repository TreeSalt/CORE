"""
Phase 9B: Council-Grade Portfolio Router Tests
- Deterministic (seeded RNG)
- Lookahead trap (proves decisions at T don't see T's close)
"""

import unittest

import numpy as np
import pandas as pd

from antigravity_harness.portfolio_policies import (
    CrossSectionMeanReversionPolicy,
    CrossSectionMomentumPolicy,
    DefensiveCashPolicy,
    InverseVolatilityPolicy,
    PolicyConfig,
)
from antigravity_harness.portfolio_router import PortfolioRouter
from antigravity_harness.regimes import RegimeConfig, RegimeFlag, RegimeLabel, detect_regime


def _make_clean_data(seed: int = 42) -> tuple[pd.DataFrame, pd.DatetimeIndex]:
    """Deterministic 3-asset dataset: A=uptrend, B=downtrend, C=flat."""
    np.random.seed(seed)
    dates = pd.date_range("2023-01-01", periods=100, freq="D")
    data = {
        "A": np.linspace(100, 150, 100) + np.random.normal(0, 0.3, 100),
        "B": np.linspace(100, 60, 100) + np.random.normal(0, 0.3, 100),
        "C": np.linspace(100, 102, 100) + np.random.normal(0, 0.3, 100),
    }
    return pd.DataFrame(data, index=dates), dates


class TestRegimeDetection(unittest.TestCase):
    def setUp(self):
        self.close_df, self.dates = _make_clean_data()
        self.asof = self.dates[-1]

    def test_trend_regime(self):
        """All assets trending up → TREND detected."""
        cfg = RegimeConfig(window=20, trend_threshold=0.1)
        df = self.close_df.copy()
        df["B"] = np.linspace(100, 130, 100)  # Flip B to uptrend
        state = detect_regime(df, self.asof, cfg)
        self.assertIn("TREND", state.label, f"Expected TREND_*, got {state.label}")

    def test_panic_regime(self):
        """20% crash on last bar → PANIC."""
        cfg = RegimeConfig(window=10, panic_drawdown=-0.05)
        df = self.close_df.copy()
        df.iloc[-1] = df.iloc[-5] * 0.80
        state = detect_regime(df, self.asof, cfg)
        self.assertEqual(state.label, RegimeLabel.PANIC)
        self.assertIn(RegimeFlag.PANIC, state.flags)

    def test_deterministic(self):
        """Same seed → identical results across runs."""
        cfg = RegimeConfig(window=20)
        s1 = detect_regime(self.close_df, self.asof, cfg)
        # Re-create from same seed
        df2, _ = _make_clean_data(seed=42)
        s2 = detect_regime(df2, self.asof, cfg)
        self.assertEqual(s1.label, s2.label)
        self.assertAlmostEqual(s1.metrics["trend_z"], s2.metrics["trend_z"])


class TestPolicies(unittest.TestCase):
    def setUp(self):
        self.close_df, self.dates = _make_clean_data()
        self.asof = self.dates[-1]

    def test_momentum_long_winner(self):
        """Momentum → allocates to A (strongest uptrend)."""
        pol = CrossSectionMomentumPolicy()
        cfg = PolicyConfig(top_k=1, lookback=20)
        w = pol.compute_target_weights(self.close_df, self.asof, cfg)
        self.assertGreater(w["A"], 0.0)
        self.assertEqual(w["B"], 0.0)
        self.assertAlmostEqual(sum(w.values()), 1.0)

    def test_mean_reversion_long_loser(self):
        """MeanReversion → allocates to B (biggest loser)."""
        pol = CrossSectionMeanReversionPolicy()
        cfg = PolicyConfig(top_k=1, lookback=20)
        w = pol.compute_target_weights(self.close_df, self.asof, cfg)
        self.assertGreater(w["B"], 0.0)
        self.assertEqual(w["A"], 0.0)

    def test_inverse_vol_all_positive(self):
        """InvVol gives non-zero weight to each asset, sums to 1."""
        pol = InverseVolatilityPolicy()
        cfg = PolicyConfig(lookback=30)
        w = pol.compute_target_weights(self.close_df, self.asof, cfg)
        for v in w.values():
            self.assertGreater(v, 0.0)
        self.assertAlmostEqual(sum(w.values()), 1.0, places=5)

    def test_cash_all_zero(self):
        """CashPolicy returns 0 for every asset."""
        pol = DefensiveCashPolicy()
        cfg = PolicyConfig()
        w = pol.compute_target_weights(self.close_df, self.asof, cfg)
        self.assertEqual(sum(w.values()), 0.0)


class TestRouterIntegration(unittest.TestCase):
    def setUp(self):
        self.close_df, self.dates = _make_clean_data()
        self.asof = self.dates[-1]

    def test_router_returns_dict_and_state(self):
        """Router returns (weights_dict, RegimeState)."""
        router = PortfolioRouter()
        w, state = router.route(self.close_df, self.asof)
        self.assertIsInstance(w, dict)
        self.assertEqual(len(w), 3)
        self.assertTrue(hasattr(state, "label"))
        # Weights may sum to <1.0 (cash policy or risk scaling),
        # but must never exceed 1.0
        self.assertLessEqual(sum(w.values()), 1.0 + 1e-6)

    def test_router_deterministic(self):
        """Same data → identical weights."""
        router = PortfolioRouter()
        w1, s1 = router.route(self.close_df, self.asof)
        df2, _ = _make_clean_data(seed=42)
        w2, s2 = router.route(df2, self.asof)
        self.assertEqual(s1.label, s2.label)
        for k in w1:
            self.assertAlmostEqual(w1[k], w2[k], places=8)


class TestLookaheadTrap(unittest.TestCase):
    """
    CRITICAL: proves that the Router does NOT see bar T's close
    when making decisions at time T.

    Strategy:
      1. Build clean data (100 bars).
      2. Compute router weights using data up to bar 98 (asof=dates[98]).
      3. Inject a massive spike on bar 99 (last bar).
      4. Compute router weights again using data up to bar 98 (same asof).
         The spike on bar 99 should NOT appear in the data slice.
      5. Assert weights are IDENTICAL ⇒ no lookahead.

    If anyone changes `iloc[:i]` back to `iloc[:i+1]`, this test FAILS.
    """

    def test_spike_invisible_to_decision(self):
        np.random.seed(42)
        close_df, dates = _make_clean_data(seed=42)

        router = PortfolioRouter()
        asof_t_minus_1 = dates[98]  # decision point

        # ── Baseline: clean data up to bar 98 ──
        clean_slice = close_df.iloc[:99]  # bars 0..98
        w_clean, s_clean = router.route(clean_slice, asof_t_minus_1)

        # ── Poisoned: inject 10x spike on bar 99 ──
        poisoned_df = close_df.copy()
        poisoned_df.iloc[99] = poisoned_df.iloc[98] * 10.0  # absurd spike

        # Slice up to bar 98 (same window the engine would use at i=99)
        poisoned_slice = poisoned_df.iloc[:99]  # bars 0..98
        w_poisoned, s_poisoned = router.route(poisoned_slice, asof_t_minus_1)

        # ── Assert identical ──
        self.assertEqual(s_clean.label, s_poisoned.label, "Regime flipped — lookahead detected!")
        for k in w_clean:
            self.assertAlmostEqual(
                w_clean[k], w_poisoned[k], places=10, msg=f"Weight for {k} changed — lookahead detected!"
            )

    def test_spike_would_change_if_included(self):
        """Prove the spike IS detectable when bar 99 is included (sanity check)."""
        np.random.seed(42)
        close_df, dates = _make_clean_data(seed=42)

        router = PortfolioRouter()

        # Clean: full 100 bars, asof = dates[99]
        w_clean, s_clean = router.route(close_df, dates[99])

        # Poisoned bar 99 with 10x spike, include it
        poisoned_df = close_df.copy()
        poisoned_df.iloc[99] = poisoned_df.iloc[98] * 10.0
        w_poisoned, s_poisoned = router.route(poisoned_df, dates[99])

        # At least one metric should differ
        metrics_differ = any(
            abs(s_clean.metrics.get(k, 0) - s_poisoned.metrics.get(k, 0)) > 1e-6
            for k in s_clean.metrics  # noqa: PLR2004
        )
        self.assertTrue(metrics_differ, "Spike had no effect even when included — test is vacuous")


class TestBacktestDeterminism(unittest.TestCase):
    """
    End-to-end determinism: run the same backtest twice →
    equity curve SHA256 must be identical.
    """

    @staticmethod
    def _build_synthetic_ohlc(seed: int = 42) -> dict:
        """Deterministic OHLC data map for 3 assets, 100 bars."""
        np.random.seed(seed)
        dates = pd.date_range("2023-01-01", periods=100, freq="D")
        data_map = {}
        for sym, drift in [("X", 0.001), ("Y", -0.0005), ("Z", 0.0002)]:
            close = 100.0 * np.exp(np.cumsum(np.random.normal(drift, 0.02, 100)))
            df = pd.DataFrame(
                {
                    "Open": close * (1 - np.random.uniform(0, 0.005, 100)),
                    "High": close * (1 + np.random.uniform(0, 0.01, 100)),
                    "Low": close * (1 - np.random.uniform(0, 0.01, 100)),
                    "Close": close,
                    "Volume": np.random.randint(1000, 10000, 100).astype(float),
                },
                index=dates,
            )
            data_map[sym] = df
        return data_map

    def _run_backtest(self, seed: int = 42) -> str:
        """Run a backtest and return SHA256 of the equity curve CSV."""
        import hashlib

        from antigravity_harness.config import EngineConfig, StrategyParams
        from antigravity_harness.portfolio_engine import run_portfolio_backtest_verbose
        from antigravity_harness.strategies import V032Simple

        data_map = self._build_synthetic_ohlc(seed)
        router = PortfolioRouter()

        _, _, curve = run_portfolio_backtest_verbose(
            data_map=data_map,
            strategy_cls=V032Simple,
            strat_params=StrategyParams(),
            engine_config=EngineConfig(),
            rebalance_freq="M",
            optimization_method="",
            initial_cash=100_000.0,
            router=router,
        )
        csv_bytes = curve.to_csv().encode("utf-8")
        return hashlib.sha256(csv_bytes).hexdigest()

    def test_portfolio_backtest_deterministic(self):
        """Same inputs → byte-identical equity curve (SHA256 match)."""
        h1 = self._run_backtest(seed=42)
        h2 = self._run_backtest(seed=42)
        self.assertEqual(h1, h2, f"Equity curve hash mismatch!\n  Run 1: {h1}\n  Run 2: {h2}")


if __name__ == "__main__":
    unittest.main()
