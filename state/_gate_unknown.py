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

# (import shimmed)

class ZOO_E2_005(Strategy):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def prepare_data(self, df, params, intelligence=None, vector_cache=None) -> pd.DataFrame:
        # Calculate the prior close
        df.loc[:, 'prior_close'] = df['close'].shift(1)
        
        # Calculate the opening gap
        df.loc[:, 'opening_gap'] = df['open'] - df['prior_close']
        
        # Calculate the percentage gap
        df.loc[:, 'percent_gap'] = df['opening_gap'] / df['prior_close']
        
        # Calculate ATR (Average True Range)
        df.loc[:, 'TR1'] = df['high'] - df['low']
        df.loc[:, 'TR2'] = (df['high'] - df['close'].shift(1)).abs()
        df.loc[:, 'TR3'] = (df['low'] - df['close'].shift(1)).abs()
        df.loc[:, 'TR'] = df[['TR1', 'TR2', 'TR3']].max(axis=1)
        df.loc[:, 'ATR'] = df['TR'].rolling(window=14).mean()
        
        # Determine entry signal based on gap > 0.5%
        df.loc[:, 'entry_signal'] = (df['percent_gap'] > 0.005)
        
        # Initialize exit signal
        df.loc[:, 'exit_signal'] = False
        
        # Logic to set exit signal within the first 2 hours of trading
        # Assuming 1 minute data, 120 minutes = 2 hours
        df.loc[:, 'time_since_open'] = df.index - df.index.normalize()
        df.loc[:, 'time_since_open_minutes'] = df['time_since_open'].dt.total_seconds() / 60
        df.loc[(df['entry_signal']) & (df['time_since_open_minutes'] <= 120), 'exit_signal'] = True
        
        # Drop intermediate columns if necessary
        df.drop(columns=['prior_close', 'opening_gap', 'percent_gap', 'TR1', 'TR2', 'TR3', 'TR', 'time_since_open', 'time_since_open_minutes'], inplace=True)
        
        return df
