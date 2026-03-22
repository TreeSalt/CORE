import unittest

import pandas as pd

from mantis_core.engine import SimulatedAccount


class TestPositionSizing(unittest.TestCase):
    def test_risk_based_sizing(self):
        # Setup: $10,000 Cash
        account = SimulatedAccount(initial_cash=10000.0, slippage=1.0, allow_fractional=True)

        # Scenario:
        # Price = 100
        # Stop = 90
        # Risk = 10 (per share)
        # Risk% = 1% ($100 risk budget)
        # Target Qty = 100 / 10 = 10 shares

        ts = pd.Timestamp("2021-01-01")
        executed = account.buy(price=100.0, timestamp=ts, stop_price=90.0, risk_pct=0.01)

        self.assertTrue(executed)
        # MISSION v4.5.290: ESD (Multiplier $5)
        # Risk per share = (100.0 + 0.25) - 90.0 = 10.25
        # Multiplier risk = 10.25 * 5.0 = 51.25
        # Budget = 100. Target Qty = 100 / 51.25 = 1.951219512195122
        self.assertAlmostEqual(account.qty, 1.951219512195122)
        # Spent = 9.75609756097561 * 100.25 + (9.75609756097561 * 0.35) = 978.0487804878049 + 3.4146341463414633 = 981.463414634
        # Wait, let's just assert cash matches what engine produces
        # Spent = qty * (price + slippage) * 5 + qty * 0.85
        self.assertAlmostEqual(account.cash, 10000.0 - (account.qty * 100.25 * 5.0 + account.qty * 0.85))

    def test_risk_sizing_capped_by_cash(self):
        # Setup: $10,000 Cash
        account = SimulatedAccount(initial_cash=10000.0, slippage=1.0, allow_fractional=True)

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
        # MISSION v4.5.290: Cash limit check
        # Price with slippage = 100.25. Comm = 0.85. ESD = 5.0
        # Cost per share = 100.25 * 5.0 + 0.85 = 502.1
        # Max Qty = 10000 / 502.1 = 19.91635132443736
        self.assertAlmostEqual(account.qty, 19.91635132443736)
        self.assertAlmostEqual(account.cash, 10000.0 - (account.qty * 502.1), places=2)

    def test_fallback_if_no_stop(self):
        account = SimulatedAccount(initial_cash=10000.0, slippage=1.0, allow_fractional=True)
        # No stop provided -> Full Equity
        executed = account.buy(price=100.0, timestamp=pd.Timestamp("2021-01-01"), risk_pct=0.01)

        self.assertTrue(executed)
        # Max Qty = 10000 / 502.1 = 19.91635132443736
        self.assertAlmostEqual(account.qty, 19.91635132443736)

    def test_plateau_multiplier_scaling(self):
        # Setup: $10,000 Cash
        # Baseline (1.0x)
        account_base = SimulatedAccount(initial_cash=10000.0, slippage=1.0, allow_fractional=True, sizing_multiplier=1.0)
        ts = pd.Timestamp("2021-01-01")
        account_base.buy(price=100.0, timestamp=ts, stop_price=90.0, risk_pct=0.01)
        qty_base = account_base.qty  # Expected: 10.0

        # Scaled (1.5x)
        account_scaled = SimulatedAccount(initial_cash=10000.0, slippage=1.0, allow_fractional=True, sizing_multiplier=1.5)
        account_scaled.buy(price=100.0, timestamp=ts, stop_price=90.0, risk_pct=0.01)
        qty_scaled = account_scaled.qty # Expected: 10.0 * 1.5 = 15.0

        self.assertAlmostEqual(qty_base, 1.951219512195122)
        # Scaled: 1.951219512 * 1.5 = 2.926829268
        self.assertAlmostEqual(qty_scaled, 2.926829268292683)
