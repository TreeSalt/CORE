
import pandas as pd
import numpy as np
try:
    from mantis_core.strategies.base import Strategy
except ImportError:
    class Strategy:
        name = "base"
        def prepare_data(self, df, params=None, intelligence=None, vector_cache=None):
            raise NotImplementedError
try:
    from mantis_core.config import StrategyParams
except ImportError:
    class StrategyParams:
        pass
class BaseStrategy(Strategy):
    pass

from typing import Optional
import pandas as pd
from mantis_core.strategies.base import BaseStrategy

class ZOO_E1_004_OpeningRangeBreakout(BaseStrategy):
    """
    VARIANT: ZOO_E1_004
    REGIME_AFFINITY: High-conviction directional days — gap-and-go sessions,
                     FOMC follow-through, earnings-driven index moves.
    ANTI_FRAGILITY_SCORE: 7/10
    """
    
    def __init__(self, allow_fractional_shares=False, max_contracts=1, no_overnight=True, max_trades_per_day=3):
        super().__init__(allow_fractional_shares, max_contracts, no_overnight, max_trades_per_day)
    
    def generate_signals(self, bars: pd.DataFrame) -> pd.Series:
        """
        Generates trading signals based on the Opening Range Breakout strategy.
        
        Parameters:
        bars (pd.DataFrame): Dataframe containing OHLCV data.
        
        Returns:
        pd.Series: Series of signals (1 for long, 0 for hold, -1 for exit).
        """
        # Ensure the data has the required columns
        required_columns = ['high', 'low', 'close', 'volume']
        if not all(col in bars.columns for col in required_columns):
            raise ValueError("Input DataFrame must contain 'high', 'low', 'close', and 'volume' columns.")
        
        # Calculate the opening range (first 6 bars after market open)
        opening_range = bars.iloc[:6]
        opening_high = opening_range['high'].max()
        opening_low = opening_range['low'].min()
        opening_range_width = opening_high - opening_low
        opening_range_volume_avg = opening_range['volume'].mean()
        
        # Calculate the volume confirmation threshold
        volume_threshold = 1.5 * opening_range_volume_avg
        
        # Initialize signal series
        signals = pd.Series(0, index=bars.index)
        
        # Determine entry conditions
        entry_condition = (bars['close'] > opening_high) & (bars['volume'] > volume_threshold)
        entry_point = bars[entry_condition].index
        
        # Determine exit conditions
        exit_condition = (bars['close'] < opening_high) & (bars['close'] > opening_low)
        exit_point = bars[exit_condition].index
        
        # Determine stop loss condition
        stop_loss_condition = (bars['close'] < (opening_high - 0.5 * opening_range_width))
        stop_loss_point = bars[stop_loss_condition].index
        
        # Set signals based on conditions
        for idx in entry_point:
            signals[idx] = 1
        
        for idx in exit_point:
            if signals[idx] == 1:
                signals[idx] = -1
        
        for idx in stop_loss_point:
            if signals[idx] == 1:
                signals[idx] = -1
        
        # Ensure no overnight positions
        signals[signals.index[-1]] = -1
        
        return signals

    def __str__(self):
        return "ZOO_E1_004_OpeningRangeBreakout"
