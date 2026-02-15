import unittest

import pandas as pd

from antigravity_harness.engine import SimulatedAccount


class TestPositionSizing(unittest.TestCase):
    def test_risk_based_sizing(self):
        # Setup: $10,000 Cash
        account = SimulatedAccount(initial_cash=10000.0, slippage=0.0, allow_fractional=True)

        # Scenario:
        # Price = 100
        # Stop = 90
        # Risk = 10 (per share)
        # Risk% = 1% ($100 risk budget)
        # Target Qty = 100 / 10 = 10 shares

        ts = pd.Timestamp("2021-01-01")
        executed = account.buy(price=100.0, timestamp=ts, stop_price=90.0, risk_pct=0.01)

        self.assertTrue(executed)
        self.assertAlmostEqual(account.qty, 10.0)
        self.assertAlmostEqual(account.cash, 9000.0)  # 10000 - (10 * 100)

    def test_risk_sizing_capped_by_cash(self):
        # Setup: $10,000 Cash
        account = SimulatedAccount(initial_cash=10000.0, slippage=0.0, allow_fractional=True)

        # Scenario:
        # Price = 100
        # Stop = 99
        # Risk = 1 (per share)
        # Risk% = 2% ($200 risk budget)
        # Target Qty = 200 / 1 = 200 shares
        # Cost = 200 * 100 = $20,000 > Cash ($10,000)
        # Should cap at $10,000 / 100 = 100 shares

        ts = pd.Timestamp("2021-01-01")
        executed = account.buy(price=100.0, timestamp=ts, stop_price=99.0, risk_pct=0.02)

        self.assertTrue(executed)
        self.assertAlmostEqual(account.qty, 100.0)
        self.assertAlmostEqual(account.cash, 0.0)

    def test_fallback_if_no_stop(self):
        account = SimulatedAccount(initial_cash=10000.0, slippage=0.0, allow_fractional=True)
        # No stop provided -> Full Equity
        executed = account.buy(price=100.0, timestamp=pd.Timestamp("2021-01-01"), risk_pct=0.01)

        self.assertTrue(executed)
        self.assertAlmostEqual(account.qty, 100.0)
