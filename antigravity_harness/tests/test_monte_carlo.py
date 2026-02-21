import unittest
from typing import NamedTuple

from antigravity_harness.metrics import monte_carlo_shuffled_drawdown


class MockTrade(NamedTuple):
    pnl_abs: float
    pnl_pct: float = 0.0

class TestMonteCarlo(unittest.TestCase):
    def test_mc_drawdown_calculation(self):
        # Case 1: Simple stable strategy
        # 10 trades, all +100
        trades_stable = [MockTrade(pnl_abs=100.0) for _ in range(10)]
        mc_dd = monte_carlo_shuffled_drawdown(trades_stable, iterations=100, initial_equity=1000.0)
        # Should be 0.0 since equity only goes up
        self.assertEqual(mc_dd, 0.0)

    def test_mc_drawdown_tail_risk(self):
        # Case 2: One big loser
        # 9 trades of +100, 1 trade of -500
        # Best sequence: 9 * 100 then -500 -> MaxDD = 500 / 1900 = 26%
        # Worst sequence: -500 then 9 * 100 -> MaxDD = 500 / 1000 = 50%
        trades_risky = [MockTrade(pnl_abs=100.0) for _ in range(9)] + [MockTrade(pnl_abs=-500.0)]
        
        mc_dd_95 = monte_carlo_shuffled_drawdown(trades_risky, iterations=200, initial_equity=1000.0)
        
        # We expect MC Drawdown to be significantly higher than a lucky backtest sequence
        # Percentile 95 of these shuffles will likely be near the 50% mark
        self.assertGreater(mc_dd_95, 0.26)
        self.assertLessEqual(mc_dd_95, 0.501)

    def test_empty_trades(self):
        self.assertEqual(monte_carlo_shuffled_drawdown([], iterations=10), 0.0)

if __name__ == "__main__":
    unittest.main()
