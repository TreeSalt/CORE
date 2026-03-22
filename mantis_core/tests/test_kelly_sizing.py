import unittest

import pandas as pd

from mantis_core.engine import SimulatedAccount
from mantis_core.metrics import kelly_fraction
from mantis_core.models import Trade


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
            slippage=1.0, 
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
        
        # MISSION v4.5.290: ESD (Multiplier $5)
        # Risk amount = 20000 * 0.1 = 2000
        # Risk per contract = (100.25 - 95.0) * 5.0 = 26.25
        # Target Qty = 2000 / 26.25 = 76.19
        # Max Qty (Cash Limit) = 20000 / (100.25 * 5.0 + 0.85) = 20000 / 502.1 = 39.83270264887472
        self.assertAlmostEqual(acc.qty, 39.83270264887472, places=5)

if __name__ == "__main__":
    unittest.main()
