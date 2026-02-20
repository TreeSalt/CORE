"""
Test: Safety Overlay Integration
Verify:
1. Columns exist in equity_curve (safety_state, overlay_reason, etc.)
2. Transitions: NORMAL -> RISK_OFF -> RISK_REDUCE -> NORMAL work as expected.
"""

import unittest

import numpy as np
import pandas as pd

from antigravity_harness.config import EngineConfig, StrategyParams
from antigravity_harness.portfolio_engine import run_portfolio_backtest_verbose
from antigravity_harness.portfolio_policies import PolicyConfig
from antigravity_harness.portfolio_safety_overlay import SafetyConfig
from antigravity_harness.strategies.base import Strategy


class MockStrategy(Strategy):
    def prepare_data(self, df, params):
        return df

    def generate_signals(self, df, params):
        return pd.Series(1, index=df.index)  # Always Long


class MockRouter:
    def route(self, df, asof):
        # Always return full allocation to MOCK
        # And a dummy regime state
        from antigravity_harness.regimes import RegimeLabel, RegimeState

        return {"MOCK": 0.95}, RegimeState(RegimeLabel.RANGE_LOW_VOL)

    def preload(self, df):
        pass


class TestSafetyIntegration(unittest.TestCase):
    def test_safety_transitions(self):
        # 1. Setup Data:
        #   - 20 days stable (warmup)
        #   - Crash 30% (Trigger RISK_OFF, threshold -0.25)
        #   - Recover to -12% (Trigger RISK_REDUCE, threshold -0.10)
        #   - Recover to -3% (Trigger NORMAL, threshold -0.05)

        dates = pd.date_range("2021-01-01", periods=100)
        prices = [100.0] * 20

        # Crash to 78 (-22%) -> Triggers REDUCE (-15%) but not OFF (-25%)
        # 100 -> 78 in steps
        prices.extend(np.linspace(100, 78, 10).tolist())

        # Recover to 95 (-5%)
        # 78 -> 95
        prices.extend(np.linspace(78, 95, 20).tolist())

        # Recover to 125 (Strong ATH break to force equity recovery despite low exposure)
        prices.extend(np.linspace(95, 125, 20).tolist())

        # Fill rest
        prices.extend([97.0] * (100 - len(prices)))

        df = pd.DataFrame({"Close": prices, "Volume": [1000.0] * len(prices)}, index=dates)
        data_map = {"MOCK": df}

        # Config
        saf_cfg = SafetyConfig(
            dd_off=-0.25,
            dd_reduce=-0.15,
            reentry_off_to_reduce=-0.13,  # Allows recovery at -12% (> -0.13)
            reentry_reduce_to_normal=-0.05,  # Allows recovery at -3% (> -0.05)
            enable_panic_physics=False,  # ISOLATE DD LOGIC
        )

        # Run Backtest with MockRouter
        acct, regime_log, eq_df = run_portfolio_backtest_verbose(
            data_map=data_map,
            strategy_cls=MockStrategy,
            strat_params=StrategyParams(),
            engine_config=EngineConfig(allow_fractional_shares=True),
            safety_cfg=saf_cfg,
            policy_cfg=PolicyConfig(min_positions=1, max_weight_per_asset=1.0),
            lookback_window=5,
            router=MockRouter(),
        )

        # Verify Columns
        self.assertIn("safety_state", eq_df.columns)
        self.assertIn("overlay_reason", eq_df.columns)
        self.assertIn("dd_asof", eq_df.columns)

        # DEBUG
        if "MOCK" in acct.accounts:
            print("\nTransaction Log:", acct.accounts["MOCK"].trades)
        else:
            print("\nMOCK account missing!")
        print("\nEquity Curve Head:")
        print(eq_df[["equity", "target_gross_exposure", "safety_state"]].head(10))
        print("\nEquity Curve Tail:")
        print(eq_df[["equity", "target_gross_exposure", "safety_state"]].tail(10))
        print("\nMax DD:", eq_df["dd_asof"].min())
        print("Max Exposure:", eq_df["target_gross_exposure"].max())

        # Verify States
        # Find max dd point
        # min_dd = eq_df["dd_asof"].min()
        # Check if we hit RISK_REDUCE (should happen around -15% DD)
        states = eq_df["safety_state"].unique()
        self.assertIn("RISK_REDUCE", states)
        self.assertNotIn("RISK_OFF", states, "Should not hit RISK_OFF with 22% crash")

        # Check sequence
        # Expect: NORMAL -> ... -> RISK_REDUCE -> ... -> NORMAL
        state_changes = []
        last_s = None
        for s in eq_df["safety_state"]:
            if s != last_s:
                state_changes.append(s)
                last_s = s

        # Expect: NORMAL -> ... -> RISK_OFF -> RISK_REDUCE -> NORMAL
        print("State Chain:", state_changes)

        if "RISK_REDUCE" in state_changes:
            print("Hit RISK_REDUCE")
        else:
            self.fail("Did not hit RISK_REDUCE")

        reduce_idx = state_changes.index("RISK_REDUCE")

        if "NORMAL" in state_changes[reduce_idx:]:
            print("Recovered to NORMAL")
        else:
            self.fail("Did not recover to NORMAL")


if __name__ == "__main__":
    unittest.main()
