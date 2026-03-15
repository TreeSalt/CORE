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

# (import shimmed)
import pandas as pd

class VZooE4002ATRRegimeFilter(Strategy):
    def __init__(self, data, params):
        super().__init__(data, params)
        self.atr_window = params.get('atr_window', 14)
        self.atr_threshold = params.get('atr_threshold', 1.5)

    def prepare_data(self):
        # Calculate the ATR
        high_low = self.data['High'] - self.data['Low']
        high_close = abs(self.data['High'] - self.data['Close'].shift())
        low_close = abs(self.data['Low'] - self.data['Close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        self.data['ATR'] = true_range.rolling(window=self.atr_window).mean()

        # Calculate the ATR expansion rate
        self.data['ATR_Expansion_Rate'] = self.data['ATR'].pct_change()

        # Determine the regime score
        self.data['Regime_Score'] = self.data['ATR_Expansion_Rate'].rolling(window=self.atr_window).mean()

    def generate_signals(self):
        entry_signal = False
        exit_signal = (self.data['Regime_Score'] > self.atr_threshold).iloc[-1]

        atr_value = self.data['ATR'].iloc[-1]
        return entry_signal, exit_signal, atr_value
