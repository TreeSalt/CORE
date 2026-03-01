import unittest
from datetime import datetime, timezone

import pandas as pd

from antigravity_harness.engine import SimulatedAccount
from antigravity_harness.models import Trade


class TestAlphaDecay(unittest.TestCase):
    def setUp(self):
        # Base setup: Initial cash 10,000. Price 100.0. No slippage.
        self.account = SimulatedAccount(
            initial_cash=10000.0,
            slippage=1.0,
            allow_fractional=True,
            use_alpha_decay=True,
            decay_lookback_trades=5,
            decay_threshold_win_rate=0.4,
            decay_penalty_multiplier=0.5
        )
        self.ts = pd.Timestamp(datetime.now(tz=timezone.utc))

    def _inject_trade(self, pnl: float):
        """Helper to inject a finished trade directly into the history."""
        self.account.trades.append(Trade(
            entry_time=self.ts,
            exit_time=self.ts,
            entry_price=100.0,
            exit_price=100.0 + (10.0 if pnl > 0 else -10.0),
            qty=1.0,
            pnl_abs=pnl,
            pnl_pct=0.1 if pnl > 0 else -0.1,
            bars_held=1,
            symbol="MES",
            exit_reason="MOCK"
        ))

    def test_no_decay_before_lookback(self):
        """Verify normal sizing before hitting the lookback threshold."""
        # 4 consecutive losers (less than lookback of 5)
        for _ in range(4):
            self._inject_trade(-100.0)
            
        # Buy with 100% risk 
        # Price 100, Stop 90 (Risk $10/share). Max Risk = $10,000.
        # Max Qty = 10,000 / 10 = 1000 shares.
        # Max Qty by cash = 10,000 / 100 = 100 shares. 
        self.account.buy(price=100.0, timestamp=self.ts, stop_price=90.0, risk_pct=1.0)
        
        # MISSION v4.5.290: ESD (Multiplier $5)
        # Max Qty = 10000 / (100.25 * 5.0 + 0.85) = 19.91635132443736
        self.assertAlmostEqual(self.account.qty, 19.91635132443736)

    def test_decay_activation(self):
        """Verify decay penalty triggers when win rate is too low."""
        # 5 consecutive losers (hits lookback, win rate 0.0)
        for _ in range(5):
            self._inject_trade(-100.0)
            
        # Buy with 100% risk 
        # Original logic: Risk = $10,000. 
        # Decay logic: 0% win rate < 40%. Risk = $10,000 * 0.5 penalty = $5,000.
        # Risk per share = $10 (100 - 90)
        # Qty = $5000 / 10 = 500. Cash Cap = 100. 
        # Wait, if risk_pct=0.02 (2% of $10,000 = $200)
        # Let's use 2% risk: Risk = 200. With decay Risk = 100.
        # Qty = 100 / 10 = 10 shares.
        
        # Reset account cash for clean test
        self.account.cash = 10000.0
        self.account.buy(price=100.0, timestamp=self.ts, stop_price=90.0, risk_pct=0.02)
        
        # Risk = 100. RiskPerContract = 10.25 * 5.0 = 51.25. Qty = 1.9512...
        self.assertAlmostEqual(self.account.qty, 1.951219512195122)

    def test_decay_recovery(self):
        """Verify decay penalty lifts when win rate recovers."""
        # Start with 5 losers
        for _ in range(5):
            self._inject_trade(-100.0)
            
        # Add 3 winners (Buffer size 5, so last 5 trades: L, L, W, W, W -> 3/5 = 60% win rate)
        for _ in range(3):
            self._inject_trade(100.0)
            
        self.account.cash = 10000.0
        self.account.buy(price=100.0, timestamp=self.ts, stop_price=90.0, risk_pct=0.02)
        
        # Risk = 200. Qty = 200 / 51.25 = 3.902439...
        self.assertAlmostEqual(self.account.qty, 3.902439024390244)

if __name__ == "__main__":
    unittest.main()
