import unittest

import pandas as pd

from antigravity_harness.engine import SimulatedAccount


class TestFriction(unittest.TestCase):
    def test_commission_frac(self):
        # Setup: $10,000 Cash, 10bps commission
        # Buy $5000 worth. Commission = $5.
        account = SimulatedAccount(initial_cash=10000.0, slippage=0.0, allow_fractional=True)

        price = 100.0
        # 10bps = 0.0010
        comm_frac = 0.0010

        # Manually calculate expected
        # Buy 50 shares @ 100 = 5000 gross.
        # Comm = 5000 * 0.001 = 5.0
        # Total Cost = 5005.0

        # We need to simulate buy call with specific qty?
        # Account.buy calculates qty based on cash/risk.
        # Let's use default full equity for simplicity, but we want partial to verify calc easily?
        # Actually buy uses all cash by default.
        # Let's limit via volume check to force specific size? Or just check end result.

        # Scenario: Buy with limited cash to make math easy?
        # Let's just buy with full cash and check commission deduction.
        # Cash 10000.
        # Cost = Q * P * (1 + bps)
        # Q = 10000 / (100 * 1.001) = 10000 / 100.1 = 99.9000999

        executed = account.buy(price, pd.Timestamp("2021-01-01"), comm_frac=comm_frac)
        self.assertTrue(executed)

        expected_qty = 10000.0 / (100.0 * 1.001)
        self.assertAlmostEqual(account.qty, expected_qty, places=4)
        self.assertAlmostEqual(account.cash, 0.0, places=2)  # Should be spent down to near zero

    def test_commission_fixed(self):
        # Setup: $10,000 Cash, $5 fixed commission
        account = SimulatedAccount(initial_cash=10000.0, slippage=0.0, allow_fractional=True)

        price = 100.0
        comm_fixed = 5.0

        # Cost = Q * P + 5.0
        # Q = (10000 - 5) / 100 = 9995 / 100 = 99.95

        executed = account.buy(price, pd.Timestamp("2021-01-01"), comm_fixed=comm_fixed)
        self.assertTrue(executed)
        self.assertAlmostEqual(account.qty, 99.95, places=5)
        self.assertAlmostEqual(account.cash, 0.0, places=2)

    def test_volume_limit(self):
        # Setup: $1,000,000 Cash.
        # Stock Bar Volume: 10,000.
        # Price: $10.
        # Limit: 1% (0.01).
        # Max Qty = 10,000 * 0.01 = 100 shares.
        # Without limit, we'd buy 100,000 shares ($1M / $10).

        account = SimulatedAccount(initial_cash=1_000_000.0, slippage=0.0, allow_fractional=True)

        bar_volume = 10_000
        limit_pct = 0.01

        executed = account.buy(price=10.0, timestamp=pd.Timestamp("2021-01-01"), volume=bar_volume, limit_pct=limit_pct)

        self.assertTrue(executed)
        self.assertAlmostEqual(account.qty, 100.0)
        # Cash remains high
        expected_spend = 100.0 * 10.0
        self.assertAlmostEqual(account.cash, 1_000_000.0 - expected_spend)

    def test_volume_limit_on_exit(self):
        # Setup: Own 1000 shares.
        # Volume: 5000.
        # Limit: 10% (0.1) -> Max 500 shares.
        # Should sell 500, keep 500.

        account = SimulatedAccount(initial_cash=0.0, slippage=0.0, allow_fractional=True)
        account.qty = 1000.0
        account.entry_price = 10.0
        account.entry_time = pd.Timestamp("2021-01-01")

        executed = account.sell(
            price=20.0, timestamp=pd.Timestamp("2021-01-02"), reason="test", volume=5000, limit_pct=0.1
        )

        self.assertTrue(executed)
        self.assertAlmostEqual(account.qty, 500.0)  # Remaining
        self.assertAlmostEqual(account.trades[-1].qty, 500.0)  # Sold
        self.assertEqual(account.trades[-1].exit_reason, "test_partial")
