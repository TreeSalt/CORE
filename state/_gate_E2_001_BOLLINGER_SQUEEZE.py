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

# File: antigravity_harness/strategies/lab/v_zoo_zoo_e2_001/v_zoo_zoo_e2_001.py

import pandas as pd
import numpy as np
# (import shimmed)

class V_Zoo_Zoo_E2_001(Strategy):
    def prepare_data(self, df, params, intelligence=None, vector_cache=None) -> pd.DataFrame:
        # Ensure all necessary columns are present
        required_columns = ['close', 'high', 'low']
        for column in required_columns:
            if column not in df.columns:
                raise ValueError(f"Missing required column: {column}")

        # Calculate typical price
        df.loc[:, 'typical_price'] = (df.loc[:, 'high'] + df.loc[:, 'low'] + df.loc[:, 'close']) / 3

        # Calculate the 20-day standard deviation of the typical price
        window = 20
        df.loc[:, 'std_dev'] = df.loc[:, 'typical_price'].rolling(window=window).std()

        # Calculate the Bollinger Bands
        num_std_dev = 2
        df.loc[:, 'middle_band'] = df.loc[:, 'typical_price'].rolling(window=window).mean()
        df.loc[:, 'upper_band'] = df.loc[:, 'middle_band'] + (df.loc[:, 'std_dev'] * num_std_dev)
        df.loc[:, 'lower_band'] = df.loc[:, 'middle_band'] - (df.loc[:, 'std_dev'] * num_std_dev)

        # Calculate the bandwidth
        df.loc[:, 'bandwidth'] = df.loc[:, 'upper_band'] - df.loc[:, 'lower_band']

        # Calculate the 6-month low of the bandwidth
        lookback_period = 180  # Assuming 180 trading days in 6 months
        df.loc[:, 'bandwidth_6m_low'] = df.loc[:, 'bandwidth'].rolling(window=lookback_period).min()

        # Calculate the entry signal
        df.loc[:, 'entry_signal'] = (df.loc[:, 'bandwidth'] == df.loc[:, 'bandwidth_6m_low'])

        # Calculate the ATR (Average True Range)
        df.loc[:, 'true_range'] = np.maximum.reduce([
            df.loc[:, 'high'] - df.loc[:, 'low'],
            np.abs(df.loc[:, 'high'] - df.loc[:, 'close'].shift()),
            np.abs(df.loc[:, 'low'] - df.loc[:, 'close'].shift())
        ])
        df.loc[:, 'ATR'] = df.loc[:, 'true_range'].rolling(window=window).mean()

        # Calculate the exit signal (bands expand 2x)
        df.loc[:, 'exit_signal'] = (df.loc[:, 'bandwidth'] > (df.loc[:, 'bandwidth_6m_low'] * 2))

        # Drop intermediate columns
        df.drop(columns=['typical_price', 'std_dev', 'middle_band', 'upper_band', 'lower_band', 'true_range', 'bandwidth_6m_low'], inplace=True)

        # Ensure signals are booleans
        df.loc[:, 'entry_signal'] = df.loc[:, 'entry_signal'].astype(bool)
        df.loc[:, 'exit_signal'] = df.loc[:, 'exit_signal'].astype(bool)

        return df
