
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

# antigravity_harness/strategies/lab/v_zoo_E1_005_momentum_decay_harvester/v_zoo_E1_005_momentum_decay_harvester.py

import pandas as pd
from mantis_core.strategies.base import BaseStrategy

class MOMENTUM_DECAY_HARVESTER(BaseStrategy):
    """
    STRATEGY_ID: ZOO_E1_005
    VARIANT: ZOO_E1_005
    REGIME_AFFINITY: Any regime with intraday momentum spikes
    ANTI_FRAGILITY_SCORE: 8/10
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_trades_per_day = 3
        self.allow_fractional_shares = False
        self.max_contracts = 1
        self.no_overnight = True

    def generate_signals(self, bars: pd.DataFrame) -> pd.Series:
        """
        Generate trading signals based on the MOMENTUM_DECAY_HARVESTER strategy logic.

        :param bars: DataFrame containing historical price data.
        :return: Series containing the trading signals.
        """
        # Calculate the percentage change in the closing price over the last bar
        bars['pct_change'] = bars['close'].pct_change()

        # Define the momentum spike threshold dynamically (0.3%)
        momentum_threshold = 0.003

        # Identify momentum spike bars
        bars['momentum_spike'] = bars['pct_change'] > momentum_threshold

        # Calculate the high and low of the momentum spike bars
        bars['spike_high'] = bars['high'].where(bars['momentum_spike'], method='ffill')
        bars['spike_low'] = bars['low'].where(bars['momentum_spike'], method='ffill')

        # Identify consolidation bars (open within the range of the previous momentum spike)
        bars['consolidation'] = bars['open'].between(bars['spike_low'].shift(1), bars['spike_high'].shift(1))

        # Calculate the target and stop levels
        bars['target'] = bars['spike_high'].shift(1) + (bars['spike_high'].shift(1) - bars['spike_low'].shift(1)) * 0.5
        bars['stop'] = bars['low'].shift(1)

        # Generate buy signals when there is a consolidation bar following a momentum spike
        bars['signal'] = 0
        bars.loc[bars['consolidation'] & (bars['momentum_spike'].shift(1)), 'signal'] = 1

        # Ensure no overnight positions
        bars['next_open'] = bars['open'].shift(-1)
        bars.loc[bars['time'].dt.time >= pd.to_datetime('15:55').time(), 'signal'] = 0

        # Cap the number of trades per day to 3
        daily_trade_count = bars['signal'].groupby(bars['time'].dt.date).cumsum()
        bars.loc[daily_trade_count > self.max_trades_per_day, 'signal'] = 0

        return bars['signal']

# Example usage:
# strategy = MOMENTUM_DECAY_HARVESTER()
# signals = strategy.generate_signals(historical_price_data)
