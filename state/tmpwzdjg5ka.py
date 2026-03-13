
import pandas as pd
import numpy as np
try:
    from antigravity_harness.strategies.base import Strategy
except ImportError:
    class Strategy:
        name = "base"
        def prepare_data(self, df, params=None, intelligence=None, vector_cache=None):
            raise NotImplementedError
try:
    from antigravity_harness.config import StrategyParams
except ImportError:
    class StrategyParams:
        pass
class BaseStrategy(Strategy):
    pass

"""
VARIANT: ZOO_E1_003
REGIME_AFFINITY: Universal
ANTI_FRAGILITY_SCORE: 9/10
"""

import pandas as pd
from antigravity_harness.strategies.base import BaseStrategy

class ZOORegimeChameleon(BaseStrategy):
    """
    Implementation of the ZOO_E1_003 — REGIME_CHAMELEON strategy.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.allow_fractional_shares = False
        self.max_contracts = 1
        self.no_overnight = True
        self.max_trades_per_day = 3

    def generate_signals(self, bars: pd.DataFrame) -> pd.Series:
        """
        Generate trading signals based on the REGIME_CHAMELEON strategy.

        Parameters:
        bars (pd.DataFrame): DataFrame containing OHLCV data.

        Returns:
        pd.Series: Series of signals (-1, 0, 1) indicating sell, hold, buy respectively.
        """

        # Calculate ADX, EMA, and Bollinger Bands
        bars['ADX_14'] = self.calculate_adx(bars, window=14)
        bars['EMA_8'] = bars['close'].ewm(span=8, adjust=False).mean()
        bars['EMA_21'] = bars['close'].ewm(span=21, adjust=False).mean()
        bars['BB_UPPER'], bars['BB_MID'], bars['BB_LOWER'] = self.calculate_bollinger_bands(bars, window=20, num_std=2.0)

        # Initialize signals series
        signals = pd.Series(0, index=bars.index)

        # Trending regime (ADX > 25)
        trending_mask = bars['ADX_14'] > 25
        signals[trending_mask] = self.generate_trend_signals(bars[trending_mask])

        # Ranging regime (ADX < 20)
        ranging_mask = bars['ADX_14'] < 20
        signals[ranging_mask] = self.generate_mean_reversion_signals(bars[ranging_mask])

        # Transition zone (20 <= ADX <= 25) - do nothing
        transition_mask = (bars['ADX_14'] >= 20) & (bars['ADX_14'] <= 25)
        signals[transition_mask] = 0

        # Cap the number of trades per day
        daily_trade_count = signals.resample('D').apply(lambda x: (x != 0).sum())
        max_trades_per_day = self.max_trades_per_day
        for date, count in daily_trade_count.items():
            if count > max_trades_per_day:
                excess_trades = count - max_trades_per_day
                trade_dates = signals[signals != 0].loc[date].index[:excess_trades]
                signals[trade_dates] = 0

        return signals

    def calculate_adx(self, bars, window=14):
        """Calculate ADX using a custom method to avoid external library dependency."""
        high, low, close = bars['high'], bars['low'], bars['close']
        tr = high - low
        tr1 = high - close.shift(1)
        tr2 = low - close.shift(1)
        tr = pd.concat([tr, tr1, tr2], axis=1).max(axis=1)

        # Calculate DM+
        dm_plus = high - high.shift(1)
        dm_minus = low.shift(1) - low
        dm_plus = dm_plus.where((dm_plus > dm_minus) & (dm_plus > 0), 0)
        dm_minus = dm_minus.where((dm_minus > dm_plus) & (dm_minus > 0), 0)

        # Smooth DM+ and DM-
        tr_avg = tr.rolling(window=window).mean()
        dm_plus_avg = dm_plus.rolling(window=window).mean()
        dm_minus_avg = dm_minus.rolling(window=window).mean()

        # Calculate DI+
        di_plus = 100 * dm_plus_avg / tr_avg
        di_minus = 100 * dm_minus_avg / tr_avg

        # Calculate DX
        dx = 100 * abs(di_plus - di_minus) / (di_plus + di_minus)
        adx = dx.rolling(window=window).mean()

        return adx

    def calculate_bollinger_bands(self, bars, window=20, num_std=2.0):
        """Calculate Bollinger Bands using a custom method."""
        mid_band = bars['close'].rolling(window=window).mean()
        std_dev = bars['close'].rolling(window=window).std()
        upper_band = mid_band + (std_dev * num_std)
        lower_band = mid_band - (std_dev * num_std)
        return upper_band, mid_band, lower_band

    def generate_trend_signals(self, bars):
        """Generate signals based on EMA crossover in trending regime."""
        signals = pd.Series(0, index=bars.index)
        ema_8 = bars['EMA_8']
        ema_21 = bars['EMA_21']
        signals[(ema_8 > ema_21) & (ema_8.shift(1) <= ema_21.shift(1))] = 1  # Buy when EMA8 crosses above EMA21
        signals[(ema_8 < ema_21) & (ema_8.shift(1) >= ema_21.shift(1))] = -1  # Sell when EMA8 crosses below EMA21
        return signals

    def generate_mean_reversion_signals(self, bars):
        """Generate signals based on Bollinger Bands in ranging regime."""
        signals = pd.Series(0, index=bars.index)
        close = bars['close']
        bb_lower = bars['BB_LOWER']
        bb_mid = bars['BB_MID']
        bb_upper = bars['BB_UPPER']
        signals[(close < bb_lower) & (close.shift(1) >= bb_lower.shift(1))] = 1  # Buy when close is below lower band
        signals[(close > bb_upper) & (close.shift(1) <= bb_upper.shift(1))] = -1  # Sell when close breaches upper band
        signals[(close >= bb_mid) & (close.shift(1) < bb_mid.shift(1))] = -1  # Exit long at midline
        return signals

# Ensure the strategy adheres to the contract by passing the test suite
