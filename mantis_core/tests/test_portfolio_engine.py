import unittest

import numpy as np
import pandas as pd

from mantis_core.config import EngineConfig, StrategyParams
from mantis_core.portfolio_engine import run_portfolio_backtest_verbose
from mantis_core.strategies import V032Simple


class TestPortfolioEngine(unittest.TestCase):
    def setUp(self):
        # Create 2 aligned DataFrames
        dates = pd.date_range("2021-01-01", "2021-06-01", freq="D")

        # Asset A: Up trend (doubles)
        prices_a = np.linspace(100, 200, len(dates))
        self.df_a = pd.DataFrame(
            {"Open": prices_a, "High": prices_a + 1, "Low": prices_a - 1, "Close": prices_a, "Volume": 1000},
            index=dates,
        )

        # Asset B: Flat
        prices_b = np.linspace(100, 100, len(dates))
        self.df_b = pd.DataFrame(
            {"Open": prices_b, "High": prices_b + 1, "Low": prices_b - 1, "Close": prices_b, "Volume": 1000},
            index=dates,
        )

        self.data_map = {"A": self.df_a, "B": self.df_b}

        self.config = EngineConfig(
            initial_cash=100_000.0,
            slippage_per_side=0.0,  # Pure math check
            commission_rate_frac=0.0,
        )
        self.params = StrategyParams()  # Defaults

    def test_equal_weight_rebalancing(self):
        # Run backtest with Monthly rebalance, Equal Weight
        portfolio, _, _ = run_portfolio_backtest_verbose(
            self.data_map,
            V032Simple,
            self.params,
            self.config,
            rebalance_freq="ME",  # Monthly End
            optimization_method="equal_weight",
        )

        # Check Final State
        # A doubled (100 -> 200). B flat (100 -> 100).
        # We rebalanced monthly.
        # At start: 50k A, 50k B.
        # Month 1: A up 20% (120), B flat. A=60k, B=50k. Total 110k.
        # Rebal to 55k each. Sell 5k A, Buy 5k B.
        # Repeating...
        # End result: B should have accumulated significant shares (buying low/flat vs A high).
        # Portfolio Total Equity should capture the gains but dampened by rebalancing into loser B?
        # Actually rebalancing sells winners to buy losers.
        # In a trend, this UNDERPERFORMS buy-and-hold of winner.
        # But it manages risk.

        # Verify allocations at end are roughly 50/50 (because we rebalance at end of month)
        # Last rebalance was May 31. End date June 1.
        # So allocation should be very close to 0.5/0.5

        final_eq = portfolio.get_total_equity({"A": 200.0, "B": 100.0})
        val_a = portfolio.accounts["A"].total_value(200.0)
        val_b = portfolio.accounts["B"].total_value(100.0)

        alloc_a = val_a / final_eq
        alloc_b = val_b / final_eq

        print(f"Final Equity: {final_eq}")
        print(f"Alloc A: {alloc_a}, Alloc B: {alloc_b}")

        self.assertAlmostEqual(alloc_a, 0.5, delta=0.05)
        self.assertAlmostEqual(alloc_b, 0.5, delta=0.05)

    def test_inverse_volatility(self):
        # Make B volatile
        dates = self.df_b.index
        # Add noise to B's close
        noise = np.random.normal(0, 5.0, len(dates))
        self.df_b["Close"] = 100.0 + noise

        # Run
        portfolio, _, _ = run_portfolio_backtest_verbose(
            {"A": self.df_a, "B": self.df_b},  # Use modified B
            V032Simple,
            self.params,
            self.config,
            rebalance_freq="ME",
            optimization_method="inverse_volatility",
        )

        # Expect A (Low Vol) to have higher allocation than B (High Vol)
        last_price_a = self.df_a["Close"].iloc[-1]
        last_price_b = self.df_b["Close"].iloc[-1]

        val_a = portfolio.accounts["A"].total_value(last_price_a)
        val_b = portfolio.accounts["B"].total_value(last_price_b)

        print(f"InvVol: Val A {val_a}, Val B {val_b}")
        self.assertTrue(val_a > val_b)
