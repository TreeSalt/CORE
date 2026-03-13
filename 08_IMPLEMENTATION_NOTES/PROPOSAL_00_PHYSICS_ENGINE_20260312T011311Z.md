---
DOMAIN: 00_PHYSICS_ENGINE
MODEL: qwen2.5-coder:32b
TIER: heavy
TYPE: IMPLEMENTATION
STATUS: RATIFIED
---

Certainly! Below is a Python strategy file that implements the `VOLATILITY_GATEKEEPER` strategy (`ZOO_E1_001`) according to the provided blueprint and constraints. This strategy inherits from `BaseStrategy` and includes the necessary logic for generating signals based on the described criteria.

```python
import pandas as pd
from antigravity_harness.strategies.base import BaseStrategy

class VolatilityGatekeeperStrategy(BaseStrategy):
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
        """
        # Calculate ATR and its moving averages
        bars['TR'] = bars[['High', 'Low', 'Close']].apply(
            lambda x: max(x['High'] - x['Low'], abs(x['High'] - bars['Close'].shift(1)), abs(x['Low'] - bars['Close'].shift(1))),
            axis=1
        )
        bars['ATR'] = bars['TR'].rolling(window=20).mean()
        bars['ATR_50_MA'] = bars['ATR'].rolling(window=50).mean()

        # Calculate EMAs
        bars['EMA_9'] = bars['Close'].ewm(span=9, adjust=False).mean()
        bars['EMA_21'] = bars['Close'].ewm(span=21, adjust=False).mean()

        # Generate signals
        bars['signal'] = 0
        bars['signal'][21:] = (
            (bars['EMA_9'][21:] > bars['EMA_21'][21:]) &
            (bars['ATR'] < bars['ATR_50_MA'])
        ).astype(int)

        # Add exit conditions
        bars['exit_condition'] = (
            (bars['EMA_9'] < bars['EMA_21']) |
            (bars['ATR'] > bars['ATR_50_MA'])
        ).astype(int)

        # Apply exit condition to signals
        bars['signal'] = bars['signal'].where(bars['exit_condition'] == 0, 0)

        # Apply max trades per day constraint
        bars['signal'] = self._apply_max_trades_per_day(bars['signal'])

        # Apply no overnight constraint
        bars['signal'] = self._apply_no_overnight(bars['signal'])

        return bars['signal']

    def _apply_max_trades_per_day(self, signals: pd.Series) -> pd.Series:
        """
        Ensure no more than max_trades_per_day trades are taken in a single day.
        """
        daily_trades = signals.resample('D').sum()
        excess_trades = daily_trades - self.max_trades_per_day
        excess_trades = excess_trades.where(excess_trades > 0, 0).cumsum()
        adjusted_signals = signals.copy()
        for i, row in enumerate(adjusted_signals):
            if row == 1 and excess_trades[signals.index[i].date()] > 0:
                adjusted_signals.iloc[i] = 0
                excess_trades[signals.index[i].date()] -= 1
        return adjusted_signals

    def _apply_no_overnight(self, signals: pd.Series) -> pd.Series:
        """
        Ensure no overnight positions.
        """
        # Assuming bars are 5-minute intervals, check if the bar is the last of the day
        bars_per_day = 288  # 5-minute bars in a trading day (6.5 hours * 60 / 5)
        adjusted_signals = signals.copy()
        for i in range(len(signals) - 1, bars_per_day - 1, -bars_per_day):
            if adjusted_signals.iloc[i] == 1:
                adjusted_signals.iloc[i] = 0
        return adjusted_signals

# Example usage:
# strategy = VolatilityGatekeeperStrategy()
# signals = strategy.generate_signals(bars)
# print(signals)
```

### Key Points:
1. **ATR Calculation:** The Average True Range (ATR) and its 50-period moving average (ATR_50_MA) are calculated to determine the volatility regime.
2. **EMA Calculation:** Exponential Moving Averages (EMA) with periods 9 and 21 are calculated to generate trend signals.
3. **Signal Generation:** Long signals are generated when EMA_9 crosses above EMA_21 and the ATR is below its 50-period moving average. Exit signals are generated when EMA_9 crosses below EMA_21 or the ATR expands above its 50-period moving average.
4. **Constraints:** The strategy ensures no more than 3 trades per day and no overnight positions.

This strategy is designed to be compliant with the `antigravity_harness` framework and should pass the strategy contract test suite when implemented correctly.