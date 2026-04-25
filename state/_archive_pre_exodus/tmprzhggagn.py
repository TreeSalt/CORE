
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

class V_ZOO_ZOO_E2_004(mantis_core.strategies.base.Strategy):
    def prepare_data(self, df, params, intelligence=None, vector_cache=None) -> pd.DataFrame:
        # Calculate the 20-bar average volume
        df.loc[:, 'avg_volume_20'] = df['volume'].rolling(window=20).mean()
        
        # Calculate the 20-bar ATR (Average True Range)
        df.loc[:, 'high_low'] = df['high'] - df['low']
        df.loc[:, 'high_close'] = abs(df['high'] - df['close'].shift(1))
        df.loc[:, 'low_close'] = abs(df['low'] - df['close'].shift(1))
        df.loc[:, 'tr'] = df[['high_low', 'high_close', 'low_close']].max(axis=1)
        df.loc[:, 'ATR'] = df['tr'].rolling(window=20).mean()
        
        # Identify volume spikes (volume exceeds 3x 20-bar average)
        df.loc[:, 'volume_spike'] = (df['volume'] > 3 * df['avg_volume_20'])
        
        # Identify new price highs
        df.loc[:, 'new_high'] = (df['close'] > df['close'].rolling(window=20).max())
        
        # Generate entry signal: SHORT when volume spikes and new high is made
        df.loc[:, 'entry_signal'] = (df['volume_spike'] & df['new_high'])
        
        # Generate exit signal: None specified, so set to False
        df.loc[:, 'exit_signal'] = False
        
        # Clean up intermediate columns if necessary
        df.drop(columns=['high_low', 'high_close', 'low_close', 'tr', 'avg_volume_20'], inplace=True)
        
        return df
