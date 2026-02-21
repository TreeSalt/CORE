import unittest

import numpy as np
import pandas as pd

from antigravity_harness.config import EngineConfig, StrategyParams
from antigravity_harness.engine import run_backtest


class TestRegimeStop(unittest.TestCase):
    def test_regime_aware_stop_scaling(self):
        np.random.seed(42)  # Deterministic dataset to prevent test pollution
        # Create a synthetic dataset that triggers a HIGH_VOL regime
        dates = pd.date_range("2024-01-01", periods=150)
        
        closes = [100.0]
        for i in range(1, 150):
            noise = 0.001 if i < 100 else 0.05
            ret = (np.random.randn() * noise)
            closes.append(closes[-1] * (1 + ret))
            
        df = pd.DataFrame({
            "Open": closes,
            "High": [c * 1.01 for c in closes],
            "Low": [c * 0.99 for c in closes],
            "Close": closes,
            "Volume": [1000] * 150
        }, index=dates)
        
        sig = pd.DataFrame(index=df.index)
        sig["entry_signal"] = False
        sig["exit_signal"] = False
        sig["ATR"] = 1.0
        
        sig.iloc[40, sig.columns.get_loc("entry_signal")] = True
        sig.iloc[110, sig.columns.get_loc("entry_signal")] = True
        
        params = StrategyParams(
            stop_atr=2.0,
            stop_mult_trend_high_vol=5.0,
            stop_mult_range_high_vol=5.0,
            stop_mult_panic=5.0,
            risk_per_trade=0.01,
            disable_stop=False
        )
        engine_cfg = EngineConfig(initial_cash=10000.0)
        prepared = sig.copy()
        res = run_backtest(df, prepared, params, engine_cfg)
        
        trace = res.trace
        stop_41 = trace.iloc[41]["stop_price"]
        stop_111 = trace.iloc[111]["stop_price"]
        open_41 = df.iloc[41]["Open"]
        open_111 = df.iloc[111]["Open"]
        
        dist_41 = open_41 - stop_41
        dist_111 = open_111 - stop_111
        
        if pd.isna(dist_111):
            print("TRACE AROUND 111:")
            print(trace.iloc[105:115][["cash", "qty", "stop_price"]])
            print("TRADES:")
            for t in res.trades:
                print(t)
        
        self.assertGreater(dist_111, dist_41)
        self.assertAlmostEqual(dist_111 / dist_41, 5.0, delta=0.5)

if __name__ == "__main__":
    unittest.main()
