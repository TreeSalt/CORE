import unittest

import numpy as np
import pandas as pd

from mantis_core.regimes import RegimeConfig, RegimeLabel, compute_regime_indicators, infer_regimes_from_metrics


class TestMLRegimes(unittest.TestCase):
    def test_ml_clustering_end_to_end(self):
        np.random.seed(42)
        dates = pd.date_range("2023-01-01", periods=1000)
        
        # Synthesize varying market conditions
        closes = [100.0]
        for i in range(1, 1000):
            if i < 300:
                # low vol range
                ret = np.random.randn() * 0.005
            elif i < 600:
                # high vol trend up
                ret = 0.002 + np.random.randn() * 0.02
            elif i < 800:
                # panic crash
                ret = -0.01 + np.random.randn() * 0.04
            else:
                # low vol trend up
                ret = 0.001 + np.random.randn() * 0.005
                
            closes.append(closes[-1] * (1 + ret))
            
        df = pd.DataFrame({
            "Open": closes,
            "High": [c * 1.01 for c in closes],
            "Low": [c * 0.99 for c in closes],
            "Close": closes,
            "Volume": [1000] * 1000
        }, index=dates)

        # 1. Base config (Schmitt)
        cfg_static = RegimeConfig(window=20)
        metrics_df = compute_regime_indicators(df[["Close"]], cfg_static)
        states_static = infer_regimes_from_metrics(metrics_df, cfg_static)
        
        # 2. ML config
        cfg_ml = RegimeConfig(
            window=20, 
            use_ml_classification=True, 
            ml_clusters=4, 
            ml_fit_window=200
        )
        states_ml = infer_regimes_from_metrics(metrics_df, cfg_ml)
        
        self.assertEqual(len(states_static), len(states_ml))
        self.assertEqual(len(states_ml), 1000)
        
        # Verify ML states have assigned labels mapped from K-Means
        active_labels = {s.label for s in states_ml[250:]} # Skip warmup + initial fit window
        self.assertIn(RegimeLabel.PANIC, active_labels)
        
        # Ensure it's not all UNKNOWN
        self.assertNotEqual(active_labels, {RegimeLabel.UNKNOWN})
        
        # It should partition into various labels
        self.assertTrue(len(active_labels) > 2)

if __name__ == "__main__":
    unittest.main()
