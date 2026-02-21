import unittest
import pandas as pd
import numpy as np
from pathlib import Path

from antigravity_harness.config import EngineConfig, StrategyParams
from antigravity_harness.engine import run_backtest
from antigravity_harness.models import SimulationContext, BacktestResult
from antigravity_harness.data.sentiment_feed import SentimentFeed

class TestSentimentAlpha(unittest.TestCase):
    def setUp(self):
        np.random.seed(42)
        dates = pd.date_range("2023-01-01", periods=100)
        # Avoid zero or negative prices which break sizing
        closes = 100.0 + np.cumsum(np.random.randn(100))
        self.df = pd.DataFrame({
            "Open": closes,
            "High": closes + 5.0,
            "Low": closes - 5.0,
            "Close": closes,
            "Volume": 1500.0
        }, index=dates)
        
        self.prepared = self.df.copy()
        
        # Create alternating valid entries and exits
        seq = np.arange(100)
        self.prepared["entry_signal"] = (seq % 10 == 0) # Enter every 10 bars
        self.prepared["exit_signal"] = (seq % 10 == 5)  # Exit 5 bars later
        self.prepared["ATR"] = 2.0
        
        self.engine_cfg = EngineConfig(
            initial_cash=150000.0, 
            warmup_extra_bars=1,
            volume_limit_pct=1.0 
        )

    def test_sentiment_baseline_vs_boosted(self):
        # 1. Baseline Run (No Sentiment)
        params_base = StrategyParams(
            risk_per_trade=0.02, 
            cooldown_bars=0,
            use_sentiment=False
        )
        res_base: BacktestResult = run_backtest(
            df=self.df,
            prepared=self.prepared,
            params=params_base,
            engine_cfg=self.engine_cfg,
        )
        
        # 2. Boosted Run (Max Greed)
        params_boost = StrategyParams(
            risk_per_trade=0.02, 
            cooldown_bars=0,
            use_sentiment=True,
            sentiment_threshold=0.5,
            sentiment_sizing_multiplier=2.0
        )
        
        # Inject extreme positive sentiment (+1.0)
        sentiment_series = pd.Series(1.0, index=self.df.index)
        feed = SentimentFeed(sentiment_series)
        
        intel = {"sentiment": feed.data}
        
        res_boost: BacktestResult = run_backtest(
            df=self.df,
            prepared=self.prepared,
            params=params_boost,
            engine_cfg=self.engine_cfg,
            intelligence=intel
        )
        
        self.assertTrue(len(res_base.trades) > 0)
        self.assertTrue(len(res_boost.trades) > 0)
        
        qty_base = res_base.trades[0].qty
        qty_boost = res_boost.trades[0].qty
        
        self.assertAlmostEqual(qty_boost, qty_base * 2.0, places=2)

    def test_sentiment_panic_restriction(self):
        # 3. Restricted Run (Max Fear)
        params_panic = StrategyParams(
            risk_per_trade=0.02, 
            cooldown_bars=0,
            use_sentiment=True,
            sentiment_threshold=0.5,
            sentiment_sizing_multiplier=2.0
        )
        
        # Inject extreme negative sentiment (-1.0)
        sentiment_series = pd.Series(-1.0, index=self.df.index)
        feed = SentimentFeed(sentiment_series)
        intel = {"sentiment": feed.data}
        
        res_panic: BacktestResult = run_backtest(
            df=self.df,
            prepared=self.prepared,
            params=params_panic,
            engine_cfg=self.engine_cfg,
            intelligence=intel
        )
        
        # Baseline check
        params_base = StrategyParams(risk_per_trade=0.02, cooldown_bars=0, use_sentiment=False)
        res_base = run_backtest(
            df=self.df, prepared=self.prepared, params=params_base, engine_cfg=self.engine_cfg
        )
        
        self.assertTrue(len(res_base.trades) > 0)
        self.assertTrue(len(res_panic.trades) > 0)

        qty_base = res_base.trades[0].qty
        qty_panic = res_panic.trades[0].qty
        self.assertAlmostEqual(qty_panic, qty_base * 0.5, places=2)

if __name__ == "__main__":
    unittest.main()
