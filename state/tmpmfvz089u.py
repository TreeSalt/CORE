
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

from mantis_core.strategies.base import BaseStrategy
import pandas as pd

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
        # Calculate ATR and its moving averages
        bars['H-L'] = bars['High'] - bars['Low']
        bars['H-PC'] = abs(bars['High'] - bars['Close'].shift(1))
        bars['L-PC'] = abs(bars['Low'] - bars['Close'].shift(1))
        bars['TR'] = bars[['H-L', 'H-PC', 'L-PC']].max(axis=1)
        bars['ATR'] = bars['TR'].rolling(window=20).mean()
        bars['ATR_50MA'] = bars['ATR'].rolling(window=50).mean()

        # Calculate EMAs
        bars['EMA_9'] = bars['Close'].ewm(span=9, adjust=False).mean()
        bars['EMA_21'] = bars['Close'].ewm(span=21, adjust=False).mean()

        # Determine entry and exit conditions
        bars['entry_signal'] = (bars['ATR'] < bars['ATR_50MA']) & (bars['EMA_9'] > bars['EMA_21']) & (bars['EMA_9'].shift(1) <= bars['EMA_21'].shift(1))
        bars['exit_signal'] = (bars['EMA_9'] < bars['EMA_21']) | (bars['ATR'] > bars['ATR_50MA'])

        # Generate signals
        signals = pd.Series(0, index=bars.index)
        signals[bars['entry_signal']] = 1
        signals[bars['exit_signal']] = -1

        return signals

    def on_trade(self, trade):
        # Ensure no overnight positions
        if self.no_overnight and self.current_position and self.current_position.is_open and self.current_position.entry_time.date() != self.current_bar_time.date():
            self.close_position()

        # Ensure max trades per day
        if self.trades_count >= self.max_trades_per_day:
            return

        # Execute trades based on signals
        if trade.signal == 1:
            self.buy()
        elif trade.signal == -1:
            self.close_position()

        # Set hard stop
        if self.current_position:
            self.set_hard_stop(2 * self.current_position.atr)
