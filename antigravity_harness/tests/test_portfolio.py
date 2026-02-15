import unittest

import pandas as pd

from antigravity_harness.portfolio import PortfolioAccount


class TestPortfolio(unittest.TestCase):
    def test_initial_allocation(self):
        # 100k Portfolio
        port = PortfolioAccount(initial_cash=100_000.0)
        port.add_asset("SPY", slippage=0.0)
        port.add_asset("TLT", slippage=0.0)

        # Initial: 100k Cash, 0 Assets
        prices = {"SPY": 100.0, "TLT": 100.0}
        self.assertEqual(port.get_total_equity(prices), 100_000.0)

        # Rebalance: 60/40
        targets = {"SPY": 0.6, "TLT": 0.4}
        ts = pd.Timestamp("2021-01-01")
        port.rebalance(targets, prices, ts)

        # Check SPY: 60k / 100 = 600 shares
        self.assertAlmostEqual(port.accounts["SPY"].qty, 600.0)

        # Check TLT: 40k / 100 = 400 shares
        self.assertAlmostEqual(port.accounts["TLT"].qty, 400.0)

        # Check Cash: Should be near 0
        self.assertAlmostEqual(port.global_cash, 0.0)

        # Default slippage is 0.001. but we set to 0.0
        # Cost = Qty * Price
        # qty = cash / price = 60000 / 100 = 600.
        self.assertAlmostEqual(port.accounts["SPY"].qty, 600.0)

    def test_rebalancing_logic(self):
        # Start with 50/50
        port = PortfolioAccount(initial_cash=20_000.0)
        port.add_asset("A", slippage=0.0)
        port.add_asset("B", slippage=0.0)

        prices = {"A": 100.0, "B": 100.0}
        port.rebalance({"A": 0.5, "B": 0.5}, prices, pd.Timestamp("2021-01-01"))

        # Should have 100 of each
        self.assertAlmostEqual(port.accounts["A"].qty, 100.0)
        self.assertAlmostEqual(port.accounts["B"].qty, 100.0)

        # MARKET MOVE
        # A doubles to 200 (Value 20k). B stays 100 (Value 10k).
        # Portfolio Value = 30k.
        # Target 50/50: 15k each.
        # A needs to sell 5k. (From 20k to 15k). Qty sell = 5000 / 200 = 25.
        # B needs to buy 5k. (From 10k to 15k). Qty buy 5000 / 100 = 50.

        prices_new = {"A": 200.0, "B": 100.0}
        port.rebalance({"A": 0.5, "B": 0.5}, prices_new, pd.Timestamp("2021-01-02"))

        # Verification
        # A: Start 100. Sell 25. End 75.
        self.assertAlmostEqual(port.accounts["A"].qty, 75.0)

        # B: Start 100. Buy 50 (with proceeds). End 150.
        self.assertAlmostEqual(port.accounts["B"].qty, 150.0)

        # Cash check
        self.assertAlmostEqual(port.global_cash, 0.0)

    def test_cash_injection(self):
        # Scenario: Cash sits in global, not fully allocated
        port = PortfolioAccount(initial_cash=10_000.0)
        port.add_asset("A", slippage=0.0)

        prices = {"A": 100.0}
        # Allocate 50%
        port.rebalance({"A": 0.5}, prices, pd.Timestamp("2021-01-01"))

        # 5000 in A (50 shares), 5000 in cash
        self.assertAlmostEqual(port.accounts["A"].qty, 50.0)
        self.assertAlmostEqual(port.global_cash, 5000.0)
