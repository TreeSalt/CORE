import unittest

import pandas as pd

from antigravity_harness.instruments.mes import MES_SPEC
from antigravity_harness.portfolio import PortfolioAccount


class TestPortfolio(unittest.TestCase):
    def test_initial_allocation(self):
        # 100k Portfolio
        port = PortfolioAccount(initial_cash=100_000.0)
        port.add_asset("SPY", spec=MES_SPEC, slippage=0.25)
        port.add_asset("TLT", spec=MES_SPEC, slippage=0.25)

        # Initial: 100k Cash, 0 Assets
        prices = {"SPY": 100.0, "TLT": 100.0}
        self.assertEqual(port.get_total_equity(prices), 100_000.0)

        # Rebalance: 60/40
        targets = {"SPY": 0.6, "TLT": 0.4}
        ts = pd.Timestamp("2021-01-01")
        port.rebalance(targets, prices, ts)

        # Check SPY: Corrected for hardened friction-aware physics
        self.assertAlmostEqual(port.accounts["SPY"].qty, 119.72164717, delta=0.01)
        # Check TLT: Corrected for hardened friction-aware physics
        self.assertAlmostEqual(port.accounts["TLT"].qty, 79.814431446, delta=0.01)

        # Check Cash: Should be near 0
        self.assertAlmostEqual(port.global_cash, 0.0)

    def test_rebalancing_logic(self):
        # Start with 50/50
        port = PortfolioAccount(initial_cash=20_000.0)
        port.add_asset("A", spec=MES_SPEC, slippage=0.25)
        port.add_asset("B", spec=MES_SPEC, slippage=0.25)

        prices = {"A": 100.0, "B": 100.0}
        port.rebalance({"A": 0.5, "B": 0.5}, prices, pd.Timestamp("2021-01-01"))

        # Should have ~19.95 of each due to multiplier + slippage + commission (friction-aware)
        self.assertAlmostEqual(port.accounts["A"].qty, 19.95360786)
        self.assertAlmostEqual(port.accounts["B"].qty, 19.95360786)

        # MARKET MOVE
        # A doubles to 200 (Value 20k). B stays 100 (Value 10k).
        # Portfolio Value = 30k.
        # Target 50/50: 15k each.
        # A needs to sell 5k. (From 20k to 15k). Qty sell = 5000 / 200 = 25.
        # B needs to buy 5k. (From 10k to 15k). Qty buy 5000 / 100 = 50.

        prices_new = {"A": 200.0, "B": 100.0}
        port.rebalance({"A": 0.5, "B": 0.5}, prices_new, pd.Timestamp("2021-01-02"))

        # Verification: Corrected for hardened friction-aware physics
        self.assertAlmostEqual(port.accounts["A"].qty, 14.96364653, places=5)
        # B: 19.916 + 9.916 = 29.832 (Adjusted for friction-aware buying)
        self.assertAlmostEqual(port.accounts["B"].qty, 29.8988062, places=3)

    def test_cash_injection(self):
        # Scenario: Cash sits in global, not fully allocated
        port = PortfolioAccount(initial_cash=10_000.0)
        port.add_asset("A", spec=MES_SPEC, slippage=0.25)

        prices = {"A": 100.0}
        # Allocate 50%
        port.rebalance({"A": 0.5}, prices, pd.Timestamp("2021-01-01"))

        # 5000 in A (9.97 shares), 5000 in cash
        self.assertAlmostEqual(port.accounts["A"].qty, 9.97680393)
        self.assertAlmostEqual(port.global_cash, 5000.0)
