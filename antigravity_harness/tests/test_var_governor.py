import unittest

import pandas as pd

from antigravity_harness.engine import SimulatedAccount
from antigravity_harness.metrics import calculate_var


class TestVarGovernor(unittest.TestCase):
    def test_calculate_var_logic(self):
        # Create a series of returns with known distributions
        dates = pd.date_range("2024-01-01", periods=100)
        equity = [10000.0]
        for i in range(1, 100):
            # Normal day: +0.5%
            # Bad day: -4% (every 10th day)
            ret = -0.04 if i % 10 == 0 else 0.005
            equity.append(equity[-1] * (1 + ret))
            
        s = pd.Series(equity, index=dates)
        
        # 95% VaR should capture the impact of the -4% moves
        var_95 = calculate_var(s, confidence=0.95)
        self.assertAlmostEqual(var_95, 0.04, places=4)

    def test_simulated_account_var_scaling(self):
        # Setup account with VaR limit = 2%
        acc = SimulatedAccount(
            initial_cash=10000.0,
            slippage=0.0,
            allow_fractional=True,
            var_limit_pct=0.02, # 2% Limit
            var_confidence=0.95,
            var_lookback=20
        )
        
        # Inject some bad history to spike VaR
        equity = 10000.0
        acc.equity_history = [equity]
        for i in range(20):
            ret = -0.05 if i < 2 else 0.001
            equity *= (1 + ret)
            acc.equity_history.append(equity)
            
        current_equity = acc.total_value(100.0)
        acc.buy(price=100.0, timestamp=pd.Timestamp("2024-02-01"), stop_price=90.0, risk_pct=0.05)
        
        # Risk per share = 10 
        # Scaled risk factor = 0.02 / 0.05 = 0.4
        # Expected qty = (current_equity * 0.05 * 0.4) / 10
        expected_qty = (current_equity * 0.02) / 10.0
        
        self.assertAlmostEqual(acc.qty, expected_qty, places=2)

if __name__ == "__main__":
    unittest.main()
