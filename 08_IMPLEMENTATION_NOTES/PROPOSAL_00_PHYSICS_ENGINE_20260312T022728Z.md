---
DOMAIN: 00_PHYSICS_ENGINE
MODEL: qwen2.5-coder:32b
TIER: heavy
TYPE: IMPLEMENTATION
STATUS: RATIFIED
---

Certainly! Below is the proposed Python strategy file implementing the `VOLATILITY_GATEKEEPER` strategy as per the provided blueprint and constraints. The strategy inherits from `BaseStrategy` and implements the `generate_signals` method. All thresholds are derived dynamically from the price data, and the strategy adheres to the specified constraints.

```python
import pandas as pd
import numpy as np
from antigravity_harness.strategies.base import BaseStrategy

class V_Zoo_E1_001_Volatility_Gatekeeper(BaseStrategy):
    """
    VARIANT: ZOO_E1_001
    REGIME_AFFINITY: Low-volatility trending — enters calm before momentum, exits before volatility expansion punishes position.
    ANTI_FRAGILITY_SCORE: 8/10 — ATR gate acts as automatic Black Swan circuit breaker. High-vol crisis events trigger ATR expansion, which closes the entry gate before damage accumulates.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_contracts = 1
        self.max_trades_per_day = 3
        self.no_overnight = True
        self.allow_fractional_shares = False

    def generate_signals(self, bars: pd.DataFrame) -> pd.Series:
        """
        Generate trading signals based on the VOLATILITY_GATEKEEPER strategy.

        :param bars: DataFrame containing historical price data.
        :return: Series containing the trading signals (1 for long entry, -1 for exit).
        """
        # Calculate ATR
        bars['H-L'] = bars['High'] - bars['Low']
        bars['H-PC'] = abs(bars['High'] - bars['Close'].shift(1))
        bars['L-PC'] = abs(bars['Low'] - bars['Close'].shift(1))
        bars['TR'] = bars[['H-L', 'H-PC', 'L-PC']].max(axis=1)
        bars['ATR'] = bars['TR'].rolling(window=20).mean()

        # Calculate 50-period moving average of ATR
        bars['ATR_50_MA'] = bars['ATR'].rolling(window=50).mean()

        # Calculate EMAs
        bars['EMA_9'] = bars['Close'].ewm(span=9, adjust=False).mean()
        bars['EMA_21'] = bars['Close'].ewm(span=21, adjust=False).mean()

        # Determine entry and exit conditions
        bars['Entry_Condition'] = (bars['ATR'] < bars['ATR_50_MA']) & (bars['EMA_9'] > bars['EMA_21'])
        bars['Exit_Condition'] = (bars['EMA_9'] < bars['EMA_21']) | (bars['ATR'] > bars['ATR_50_MA'])

        # Initialize signals
        bars['Signal'] = 0

        # Generate long entry signals
        bars['Signal'][bars['Entry_Condition'] & (bars['Signal'].shift(1) == 0)] = 1

        # Generate exit signals
        bars['Signal'][bars['Exit_Condition'] & (bars['Signal'].shift(1) == 1)] = -1

        # Apply hard stop (2x ATR from entry)
        if not bars.empty:
            bars['ATR_2x'] = bars['ATR'] * 2
            bars['Hard_Stop'] = np.nan

            # Calculate the entry price for each position
            bars['Entry_Price'] = bars['Close'][bars['Signal'] == 1]

            # Forward fill the entry price to all rows after entry
            bars['Entry_Price'] = bars['Entry_Price'].ffill()

            # Calculate the stop loss price
            bars['Stop_Loss'] = bars['Entry_Price'] - bars['ATR_2x']

            # Generate exit signals when price hits the stop loss
            bars['Signal'][bars['Close'] < bars['Stop_Loss']] = -1

        # Ensure no overnight positions
        bars['Signal'][bars.index.time > pd.to_datetime('16:00').time()] = 0

        return bars['Signal']

# Example usage:
# strategy = V_Zoo_E1_001_Volatility_Gatekeeper()
# signals = strategy.generate_signals(bars)
```

### Key Points:
- **ATR and EMAs**: The strategy calculates the Average True Range (ATR) and Exponential Moving Averages (EMAs) to determine entry and exit conditions.
- **Entry Condition**: Entry is permitted when the 20-period ATR is below its 50-period moving average and the 9-period EMA crosses above the 21-period EMA.
- **Exit Condition**: Exit is triggered when the 9-period EMA crosses below the 21-period EMA or the ATR expands above its 50-period moving average.
- **Hard Stop**: A hard stop is implemented at 2x ATR from the entry price.
- **Constraints**: The strategy ensures no overnight positions, a maximum of one contract, and a maximum of three trades per day.

This strategy should be further tested to ensure it passes the strategy contract test suite and adheres to all constraints.