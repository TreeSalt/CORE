import unittest

import pandas as pd

from mantis_core.config import EngineConfig, StrategyParams
from mantis_core.engine import run_backtest
from mantis_core.strategies.base import Strategy


class MockVolumeStrategy(Strategy):
    def prepare_data(self, df, params):
        # Entry signal on every bar to test sizing
        df = df.copy()
        df["entry_signal"] = True
        df["exit_signal"] = False
        df["ATR"] = 1.0
        return df


class TestVolumeLeak(unittest.TestCase):
    def test_volume_limit_physics(self):
        # Create data where Bar 0 has high volume and Bar 1 has low volume
        dates = pd.date_range("2020-01-01", periods=10, freq="D")
        df = pd.DataFrame(
            {
                "Open": [100.0] * 10,
                "High": [105.0] * 10,
                "Low": [95.0] * 10,
                "Close": [101.0] * 10,
                "Volume": [1000.0, 10.0, 10.0, 10.0, 10.0, 10.0, 10.0, 10.0, 10.0, 10.0],
            },
            index=dates,
        )

        # Engine Config: 10% volume limit, fractional shares allowed
        engine_cfg = EngineConfig(
            initial_cash=100000.0,
            volume_limit_pct=0.1,  # 10%
            allow_fractional_shares=True,
            warmup_extra_bars=0,
        )
        params = StrategyParams(disable_stop=True)
        strat = MockVolumeStrategy()

        # Run Backtest
        prepared = strat.prepare_data(df, params)
        res = run_backtest(df, prepared, params, engine_cfg)

        # Audit the first trade
        # Signal at Bar 0 -> Entry at Bar 1 Open.
        # Bar 1 Volume is 10. 10% limit = 1 unit.
        # Bar 0 Volume is 1000. 10% limit = 100 units.

        # If Physics is HARDENED (t-1): Bar 1 entry uses Bar 0 volume -> 100 units.
        # If Physics is LEAKY (t-0): Bar 1 entry uses Bar 1 volume -> 1 unit.

        first_trade = res.trades[0]
        print(f"DEBUG: First trade qty: {first_trade.qty}")

        # We expect 100 units because we use Bar 0 volume for Bar 1 Open.
        self.assertEqual(first_trade.qty, 100.0)


if __name__ == "__main__":
    unittest.main()
