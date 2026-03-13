
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

import pandas as pd

from antigravity_harness.strategies.base import Strategy

class ZOO_E2_003(Strategy):
    def prepare_data(self, df, params, intelligence=None, vector_cache=None) -> pd.DataFrame:
        # Calculate EMAs
        df.loc[:, 'ema_8'] = df['close'].ewm(span=params.get('ema_8_span', 8), adjust=False).mean()
        df.loc[:, 'ema_21'] = df['close'].ewm(span=params.get('ema_21_span', 21), adjust=False).mean()
        df.loc[:, 'ema_55'] = df['close'].ewm(span=params.get('ema_55_span', 55), adjust=False).mean()

        # Calculate ATR
        df.loc[:, 'high_low'] = df['high'] - df['low']
        df.loc[:, 'high_close'] = abs(df['high'] - df['close'].shift(1))
        df.loc[:, 'low_close'] = abs(df['low'] - df['close'].shift(1))
        df.loc[:, 'true_range'] = df[['high_low', 'high_close', 'low_close']].max(axis=1)
        df.loc[:, 'ATR'] = df['true_range'].ewm(span=params.get('atr_span', 14), adjust=False).mean()

        # Generate entry signal
        df.loc[:, 'entry_signal'] = ((df['ema_8'] > df['ema_21']) & (df['ema_21'] > df['ema_55']) & 
                                     (df['close'] < df['ema_21']))

        # Generate exit signal
        df.loc[:, 'exit_signal'] = False  # Placeholder for any specific exit logic

        return df[['entry_signal', 'exit_signal', 'ATR']]

# Example usage:
# strategy = ZOO_E2_003()
# df = pd.DataFrame({
#     'close': [...],
#     'high': [...],
#     'low': [...]
# })
# params = {
#     'ema_8_span': 8,
#     'ema_21_span': 21,
#     'ema_55_span': 55,
#     'atr_span': 14
# }
# result_df = strategy.prepare_data(df, params)
