import unittest
from typing import Any, List

import pandas as pd

from antigravity_harness.engine import SimulatedAccount
from antigravity_harness.metrics import kelly_fraction
from antigravity_harness.models import Trade

class TestKellySizing(unittest.TestCase):
    def test_kelly_fraction_calculation(self):
        # Case 1: 60% win rate, 2:1 win/loss ratio
        # K = 0.6 - (1 - 0.6) / 2 = 0.6 - 0.4 / 2 = 0.6 - 0.2 = 0.4
        trades = [
            # 6 wins (+2%)
            Trade(entry_time=pd.Timestamp("2024-01-01"), exit_time=pd.Timestamp("2024-01-02"), 
                  entry_price=100.0, exit_price=102.0, qty=1.0, pnl_abs=2.0, pnl_pct=0.02, exit_reason="signal"),
            Trade(entry_time=pd.Timestamp("2024-01-01"), exit_time=pd.Timestamp("2024-01-02"), 
                  entry_price=100.0, exit_price=102.0, qty=1.0, pnl_abs=2.0, pnl_pct=0.02, exit_reason="signal"),
            Trade(entry_time=pd.Timestamp("2024-01-01"), exit_time=pd.Timestamp("2024-01-02"), 
                  entry_price=100.0, exit_price=102.0, qty=1.0, pnl_abs=2.0, pnl_pct=0.02, exit_reason="signal"),
            Trade(entry_time=pd.Timestamp("2024-01-01"), exit_time=pd.Timestamp("2024-01-02"), 
                  entry_price=100.0, exit_price=102.0, qty=1.0, pnl_abs=2.0, pnl_pct=0.02, exit_reason="signal"),
            Trade(entry_time=pd.Timestamp("2024-01-01"), exit_time=pd.Timestamp("2024-01-02"), 
                  entry_price=100.0, exit_price=102.0, qty=1.0, pnl_abs=2.0, pnl_pct=0.02, exit_reason="signal"),
            Trade(entry_time=pd.Timestamp("2024-01-01"), exit_time=pd.Timestamp("2024-01-02"), 
                  entry_price=100.0, exit_price=102.0, qty=1.0, pnl_abs=2.0, pnl_pct=0.02, exit_reason="signal"),
            # 4 losses (-1%)
            Trade(entry_time=pd.Timestamp("2024-01-01"), exit_time=pd.Timestamp("2024-01-02"), 
                  entry_price=100.0, exit_price=99.0, qty=1.0, pnl_abs=-1.0, pnl_pct=-0.01, exit_reason="signal"),
            Trade(entry_time=pd.Timestamp("2024-01-01"), exit_time=pd.Timestamp("2024-01-02"), 
                  entry_price=100.0, exit_price=99.0, qty=1.0, pnl_abs=-1.0, pnl_pct=-0.01, exit_reason="signal"),
            Trade(entry_time=pd.Timestamp("2024-01-01"), exit_time=pd.Timestamp("2024-01-02"), 
                  entry_price=100.0, exit_price=99.0, qty=1.0, pnl_abs=-1.0, pnl_pct=-0.01, exit_reason="signal"),
            Trade(entry_time=pd.Timestamp("2024-01-01"), exit_time=pd.Timestamp("2024-01-02"), 
                  entry_price=100.0, exit_price=99.0, qty=1.0, pnl_abs=-1.0, pnl_pct=-0.01, exit_reason="signal"),
        ]
        
        k = kelly_fraction(trades)
        self.assertAlmostEqual(k, 0.4)

    def test_simulated_account_kelly_sizing(self):
        # Setup account with Kelly enabled
        acc = SimulatedAccount(
            initial_cash=20000.0, 
            slippage=0.0, 
            allow_fractional=True,
            use_kelly=True,
            kelly_multiplier=0.5, # Half Kelly
            kelly_max_risk=0.10   # 10% cap
        )
        
        # Inject some winning trades to establish an edge
        # 60% win rate, 2:1 ratio -> Kelly = 0.4
        # Half Kelly = 0.2, but capped at 0.1
        for _ in range(6):
            acc.trades.append(Trade(
                entry_time=pd.Timestamp("2024-01-01"), exit_time=pd.Timestamp("2024-01-02"), 
                entry_price=100.0, exit_price=102.0, qty=1.0, pnl_abs=2.0, pnl_pct=0.02, exit_reason="signal"
            ))
        for _ in range(4):
            acc.trades.append(Trade(
                entry_time=pd.Timestamp("2024-01-01"), exit_time=pd.Timestamp("2024-01-02"), 
                entry_price=100.0, exit_price=99.0, qty=1.0, pnl_abs=-1.0, pnl_pct=-0.01, exit_reason="signal"
            ))
            
        # Execute a buy with riskpct=0.01 (baseline)
        # Kelly should override it. 
        # Half Kelly (0.2) > Cap (0.1), so risk_pct should be 0.1
        acc.buy(price=100.0, timestamp=pd.Timestamp("2024-01-03"), stop_price=95.0, risk_pct=0.01)
        
        # Risk amount = 20000 * 0.1 = 2000
        # Risk per share = 100 - 95 = 5
        # Qty = 2000 / 5 = 400
        # Cash = 20000, max_qty_cash = 200
        # Min(400, 200) = 200
        self.assertEqual(acc.qty, 200.0)

if __name__ == "__main__":
    unittest.main()
