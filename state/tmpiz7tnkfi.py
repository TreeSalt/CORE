
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

import pandas as pd
from mantis_core.strategies.base import BaseStrategy

class VolatilityGatekeeper(BaseStrategy):
    """
    VARIANT: ZOO_E1_001
    REGIME_AFFINITY: Low-volatility trending — enters calm before momentum,
                     exits before volatility expansion punishes position.
    ANTI_FRAGILITY_SCORE: 8/10 — ATR gate acts as automatic Black Swan
                          circuit breaker. High-vol crisis events trigger ATR
                          expansion, which closes the entry gate before damage
                          accumulates.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_trades_per_day = 3
        self.no_overnight = True
        self.allow_fractional_shares = False
        self.max_contracts = 1

    def generate_signals(self, bars: pd.DataFrame) -> pd.Series:
        """
        Generate trading signals based on the VOLATILITY_GATEKEEPER strategy.
        
        Parameters:
        bars (pd.DataFrame): Historical price data with 5m bars.

        Returns:
        pd.Series: Series of signals (1 for long entry, -1 for exit).
        """
        # Calculate ATR
        high, low, close = bars['high'], bars['low'], bars['close']
        bars['TR'] = bars[['high', 'low']].max(axis=1) - bars[['high', 'low']].min(axis=1)
        bars['TR'] = pd.concat([bars['TR'], (bars['high'] - bars['close'].shift(1)).abs(), (bars['low'] - bars['close'].shift(1)).abs()], axis=1).max(axis=1)
        bars['ATR'] = bars['TR'].rolling(window=20).mean()

        # Calculate ATR's 50-period moving average
        bars['ATR_50MA'] = bars['ATR'].rolling(window=50).mean()

        # Calculate EMAs
        bars['EMA_9'] = close.ewm(span=9, adjust=False).mean()
        bars['EMA_21'] = close.ewm(span=21, adjust=False).mean()

        # Determine regime validity
        bars['regime_valid'] = bars['ATR'] < bars['ATR_50MA']

        # Determine entry signals
        bars['long_entry'] = (bars['EMA_9'] > bars['EMA_21']) & (bars['regime_valid'].shift(1))

        # Determine exit signals
        bars['exit'] = (bars['EMA_9'] < bars['EMA_21']) | (bars['ATR'] > bars['ATR_50MA'])

        # Initialize signal series
        signals = pd.Series(0, index=bars.index)

        # Apply entry and exit signals
        signals[bars['long_entry']] = 1
        signals[bars['exit']] = -1

        # Apply max_trades_per_day constraint
        daily_signals = signals.resample('D').apply(lambda x: (x == 1).sum())
        cumulative_trades = daily_signals.cumsum()
        signals = signals.where(cumulative_trades <= self.max_trades_per_day, 0)

        # Apply no_overnight constraint
        signals = signals.between_time('09:30:00', '16:00:00')

        return signals
