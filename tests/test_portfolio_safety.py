"""
Phase 9D: Tests for Safety Overlay + Concentration Caps.
All tests are deterministic (seeded) and anti-vacuous.
"""

import hashlib
import unittest

import numpy as np
import pandas as pd

from antigravity_harness.portfolio_policies import (
    PolicyConfig,
    apply_concentration_caps,
)
from antigravity_harness.portfolio_safety_overlay import (
    SafetyConfig,
    SafetyOverlay,
    SafetyState,
)


class TestDDBrake(unittest.TestCase):
    """Test portfolio DD brake triggers RISK_OFF."""

    def test_dd_brake_triggers_risk_off(self):
        """Equity drops >25% from ATH → RISK_OFF at next bar."""
        cfg = SafetyConfig(dd_off=-0.25, dd_reduce=-0.15, dd_hard=-0.40)
        overlay = SafetyOverlay(cfg)

        # Synthetic equity: 100k → 110k (ATH) → 80k (27% DD from ATH)
        equity = [100_000, 105_000, 110_000, 95_000, 85_000, 80_000]
        dates = pd.date_range("2021-01-01", periods=10, freq="D")
        close_df = pd.DataFrame({"A": np.linspace(100, 80, 10), "B": np.linspace(50, 40, 10)}, index=dates)

        # At bar i=5, equity_series[:5] = [100k..85k], ATH=110k, equity[4]=85k
        # dd = 85000/110000 - 1 = -0.2272 → RISK_REDUCE (not off yet)
        state, reason, dd, ath = overlay.evaluate(equity, close_df, 5, dates)
        self.assertEqual(state, SafetyState.RISK_REDUCE)

        # Now add bar where equity hit 80k → dd = 80000/110000 - 1 = -0.2727 → RISK_OFF
        equity_ext = equity + [78_000]
        state, reason, dd, ath = overlay.evaluate(equity_ext, close_df, 6, dates)
        self.assertEqual(state, SafetyState.RISK_OFF)
        self.assertEqual(reason, "PORTFOLIO_DD")

    def test_weights_zeroed_on_risk_off(self):
        """RISK_OFF → all weights become 0."""
        cfg = SafetyConfig()
        overlay = SafetyOverlay(cfg)
        weights = {"BTC": 0.5, "ETH": 0.3, "SOL": 0.2}
        result = overlay.apply_to_weights(weights, SafetyState.RISK_OFF)
        self.assertTrue(all(v == 0.0 for v in result.values()))

    def test_weights_scaled_on_risk_reduce(self):
        """RISK_REDUCE → weights scaled by multiplier."""
        cfg = SafetyConfig(reduce_multiplier=0.5)
        overlay = SafetyOverlay(cfg)
        weights = {"BTC": 0.4, "ETH": 0.6}
        result = overlay.apply_to_weights(weights, SafetyState.RISK_REDUCE)
        self.assertAlmostEqual(result["BTC"], 0.2)
        self.assertAlmostEqual(result["ETH"], 0.3)


class TestHardFailTrigger(unittest.TestCase):
    """Test HARD_FAIL_TRIGGER state on extreme drawdown."""

    def test_hard_fail_trigger_logs(self):
        """Equity drops >40% → HARD_FAIL_TRIGGER state."""
        cfg = SafetyConfig(dd_hard=-0.40, dd_off=-0.25, dd_reduce=-0.15, enable_panic_physics=False)
        overlay = SafetyOverlay(cfg)

        # equity[:asof_idx] → data used. We need DD at asof_idx=3.
        # equity[:3] = [100k, 100k, 55k], ATH=100k, last=55k, dd=-0.45
        equity = [100_000, 100_000, 55_000, 50_000]
        dates = pd.date_range("2021-01-01", periods=5, freq="D")
        close_df = pd.DataFrame({"A": [100, 90, 55, 50, 45], "B": [50, 45, 30, 25, 20]}, index=dates)

        state, reason, dd, ath = overlay.evaluate(equity, close_df, 3, dates)
        self.assertEqual(state, SafetyState.HARD_FAIL_TRIGGER)
        self.assertEqual(reason, "PORTFOLIO_DD")
        self.assertAlmostEqual(dd, -0.45, places=2)

        # Verify it still forces RISK_OFF behavior
        weights = {"A": 0.5, "B": 0.5}
        result = overlay.apply_to_weights(weights, state)
        self.assertTrue(all(v == 0.0 for v in result.values()))


class TestReentryHysteresis(unittest.TestCase):
    """Verify overlay does not flap between states."""

    def test_reentry_hysteresis(self):
        """
        Sequence: equity drops to RISK_OFF level, then recovers slightly.
        Should stay in RISK_OFF until DD recovers past reentry threshold.
        """
        cfg = SafetyConfig(
            dd_off=-0.25,
            dd_reduce=-0.15,
            dd_hard=-0.40,
            reentry_off_to_reduce=-0.20,
            reentry_reduce_to_normal=-0.10,
            enable_panic_physics=False,
        )
        overlay = SafetyOverlay(cfg)
        dates = pd.date_range("2021-01-01", periods=10, freq="D")
        close_df = pd.DataFrame({"A": np.ones(10) * 100, "B": np.ones(10) * 50}, index=dates)

        # Step 1: Drive into RISK_OFF. asof_idx=3, equity[:3]=[100k,100k,70k]
        # ATH=100k, last=70k, dd=-0.30
        equity_1 = [100_000, 100_000, 70_000, 68_000]
        state, _, dd, _ = overlay.evaluate(equity_1, close_df, 3, dates)
        self.assertEqual(state, SafetyState.RISK_OFF)

        # Step 2: Recovery. asof_idx=4, equity[:4]=[100k,100k,70k,78k]
        # ATH=100k, last=78k, dd=-0.22 (still below reentry_off=-0.20)
        equity_2 = [100_000, 100_000, 70_000, 78_000, 76_000]
        state, _, dd, _ = overlay.evaluate(equity_2, close_df, 4, dates)
        self.assertEqual(state, SafetyState.RISK_OFF, "Should stay RISK_OFF (hysteresis)")

        # Step 3: Full recovery. asof_idx=5, equity[:5]=[100k,100k,70k,78k,88k]
        # ATH=100k, last=88k, dd=-0.12 → above BOTH dd_reduce(-0.15) and reentry_off(-0.20) → NORMAL
        equity_3 = [100_000, 100_000, 70_000, 78_000, 92_000, 93_000]
        state, _, dd, _ = overlay.evaluate(equity_3, close_df, 5, dates)
        self.assertEqual(state, SafetyState.NORMAL, "Should recover to NORMAL")

    def test_risk_reduce_hysteresis(self):
        """RISK_REDUCE stays until DD recovers past reentry_reduce."""
        cfg = SafetyConfig(
            dd_off=-0.25,
            dd_reduce=-0.15,
            reentry_reduce_to_normal=-0.10,  # Updated param name
            enable_panic_physics=False,
        )
        overlay = SafetyOverlay(cfg)
        dates = pd.date_range("2021-01-01", periods=10, freq="D")
        close_df = pd.DataFrame({"A": np.ones(10) * 100}, index=dates)

        # Drive into RISK_REDUCE. asof_idx=3, equity[:3]=[100k,100k,82k], dd=-0.18
        equity_1 = [100_000, 100_000, 82_000, 81_000]
        state, _, _, _ = overlay.evaluate(equity_1, close_df, 3, dates)
        self.assertEqual(state, SafetyState.RISK_REDUCE)

        # Slight recovery. asof_idx=4, equity[:4]=[...,88k], dd=-0.12 (below -0.10)
        equity_2 = [100_000, 100_000, 82_000, 88_000, 87_000]
        state, _, _, _ = overlay.evaluate(equity_2, close_df, 4, dates)
        self.assertEqual(state, SafetyState.RISK_REDUCE, "Should stay RISK_REDUCE")

        # Full recovery. asof_idx=5, equity[:5]=[...,95k], dd=-0.05 (above -0.10)
        equity_3 = [100_000, 100_000, 82_000, 88_000, 95_000, 96_000]
        state, _, _, _ = overlay.evaluate(equity_3, close_df, 5, dates)
        self.assertEqual(state, SafetyState.NORMAL)


class TestConcentrationCaps(unittest.TestCase):
    """Test weight capping and position floor."""

    def test_concentration_cap_applied(self):
        """Single 1.0 weight → capped to max_weight_per_asset."""
        cfg = PolicyConfig(max_weight_per_asset=0.50, min_positions=2)
        # Single position: all-in on BTC
        weights = {"BTC": 1.0, "ETH": 0.0, "SOL": 0.0}
        result = apply_concentration_caps(weights, cfg)
        # Only 1 non-zero position < min_positions=2 → go to cash
        self.assertTrue(all(v == 0.0 for v in result.values()), "Single position should trigger cash (min_positions=2)")

    def test_cap_with_sufficient_positions(self):
        """Two positions, one exceeds cap → clamped and renormalized."""
        cfg = PolicyConfig(max_weight_per_asset=0.50, min_positions=2)
        weights = {"BTC": 0.7, "ETH": 0.3, "SOL": 0.0}
        result = apply_concentration_caps(weights, cfg)
        self.assertLessEqual(result["BTC"], 0.50 + 1e-9)
        self.assertGreater(result["ETH"], 0.0)

    def test_all_zero_passthrough(self):
        """All-cash weights pass through unchanged."""
        cfg = PolicyConfig(max_weight_per_asset=0.50, min_positions=2)
        weights = {"BTC": 0.0, "ETH": 0.0}
        result = apply_concentration_caps(weights, cfg)
        self.assertEqual(result, weights)

    def test_equal_weight_no_cap_change(self):
        """Equal weights below cap pass through unchanged."""
        cfg = PolicyConfig(max_weight_per_asset=0.50, min_positions=2)
        weights = {"BTC": 0.25, "ETH": 0.25, "SOL": 0.25, "AVAX": 0.25}
        result = apply_concentration_caps(weights, cfg)
        for k in weights:
            self.assertAlmostEqual(result[k], 0.25, places=6)


class TestDeterministicWithOverlay(unittest.TestCase):
    """Ensure full backtest with overlay is deterministic."""

    @staticmethod
    def _build_synthetic_ohlc(seed=42):
        np.random.seed(seed)
        dates = pd.date_range("2021-01-01", periods=120, freq="D")
        data_map = {}
        for sym in ["AAA", "BBB", "CCC"]:
            # Stable hash for seeding
            stable_hash = int(hashlib.sha256(sym.encode("utf-8")).hexdigest(), 16)
            np.random.seed(seed + stable_hash % 1000)
            base = 100.0
            prices = [base]
            for _ in range(119):
                ret = np.random.normal(0.001, 0.03)
                prices.append(prices[-1] * (1 + ret))
            df = pd.DataFrame(
                {
                    "Open": prices,
                    "High": [p * 1.01 for p in prices],
                    "Low": [p * 0.99 for p in prices],
                    "Close": prices,
                    "Volume": [1000] * 120,
                },
                index=dates,
            )
            data_map[sym] = df
        return data_map

    def _run_backtest(self, seed=42):
        from antigravity_harness.config import EngineConfig, StrategyParams
        from antigravity_harness.portfolio_engine import run_portfolio_backtest_verbose
        from antigravity_harness.portfolio_router import PortfolioRouter
        from antigravity_harness.strategies import V032Simple

        data_map = self._build_synthetic_ohlc(seed)
        router = PortfolioRouter()
        safety_cfg = SafetyConfig(enable_panic_physics=False)  # disable for isolation

        _, _, curve = run_portfolio_backtest_verbose(
            data_map=data_map,
            strategy_cls=V032Simple,
            strat_params=StrategyParams(),
            engine_config=EngineConfig(),
            rebalance_freq="M",
            optimization_method="",
            initial_cash=100_000.0,
            router=router,
            safety_cfg=safety_cfg,
        )
        csv_bytes = curve.to_csv().encode()
        return hashlib.sha256(csv_bytes).hexdigest()

    def test_deterministic_with_overlay(self):
        """Same inputs → byte-identical equity curve (SHA256 match) with overlay enabled."""
        h1 = self._run_backtest(seed=42)
        h2 = self._run_backtest(seed=42)
        self.assertEqual(h1, h2, f"Equity curve hash mismatch!\n  Run 1: {h1}\n  Run 2: {h2}")


if __name__ == "__main__":
    unittest.main()
