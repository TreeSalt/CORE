import pandas as pd
import numpy as np
from collections import namedtuple

class Strategy:
    name = "base"
    def prepare_data(self, df, params=None, intelligence=None, vector_cache=None):
        raise NotImplementedError
    def generate_signals(self, bars):
        raise NotImplementedError

BaseStrategy = Strategy

class StrategyParams:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
    def get(self, key, default=None):
        return getattr(self, key, default)
    def __getattr__(self, name):
        return None

import pandas as pd
import numpy as np
# (import shimmed)

class ZOO_E2_002(Strategy):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def prepare_data(self, df, params, intelligence=None, vector_cache=None) -> pd.DataFrame:
        # Calculate session VWAP
        df.loc[:, 'vwap'] = (df['volume'] * df['close']).cumsum() / df['volume'].cumsum()
        
        # Calculate mean and standard deviation of session VWAP
        df.loc[:, 'vwap_mean'] = df['vwap'].mean()
        df.loc[:, 'vwap_std'] = df['vwap'].std()
        
        # Calculate price deviation from session VWAP
        df.loc[:, 'price_deviation'] = df['close'] - df['vwap_mean']
        
        # Calculate ATR (Average True Range)
        df.loc[:, 'true_high'] = df[['high', 'vwap']].max(axis=1)
        df.loc[:, 'true_low'] = df[['low', 'vwap']].min(axis=1)
        df.loc[:, 'true_range'] = df['true_high'] - df['true_low']
        df.loc[:, 'ATR'] = df['true_range'].rolling(window=14).mean()
        
        # Generate entry signal
        df.loc[:, 'entry_signal'] = ((df['price_deviation'] > 2 * df['vwap_std']) | 
                                     (df['price_deviation'] < -2 * df['vwap_std']))
        
        # Generate exit signal
        df.loc[:, 'exit_signal'] = (df['close'] == df['vwap'])
        
        return df
