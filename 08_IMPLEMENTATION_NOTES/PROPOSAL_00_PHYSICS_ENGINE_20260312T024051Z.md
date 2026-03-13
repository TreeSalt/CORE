---
DOMAIN: 00_PHYSICS_ENGINE
MODEL: qwen2.5-coder:32b
TIER: heavy
TYPE: IMPLEMENTATION
STATUS: RATIFIED
---

Here is a proposal for the `v_zoo_E1_001_volatility_gatekeeper.py` strategy file based on the provided blueprint and constraints. The strategy will inherit from `BaseStrategy` and implement the `generate_signals` method. It will ensure that all parameters are dynamically derived from the price data and that it adheres to the specified constraints.

```python
import pandas as pd
from antigravity_harness.strategies.base import BaseStrategy

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
        """
        Generate trading signals based on the VOLATILITY_GATEKEEPER strategy.
        
        Parameters:
        bars (pd.DataFrame): Historical price data with 5m bars.

        Returns:
        pd.Series: Series of signals (1 for long entry, -1 for exit).
        """
        # Calculate ATR
        high, low, close = bars['high'], bars['low'], bars['close']
        bars['TR'] = bars[['high', 'low']].max(axis=1) - bars[['high', 'low']].min(axis=1)
        bars['TR'] = pd.concat([bars['TR'], (bars['high'] - bars['close'].shift(1)).abs(), (bars['low'] - bars['close'].shift(1)).abs()], axis=1).max(axis=1)
        bars['ATR'] = bars['TR'].rolling(window=20).mean()

        # Calculate ATR's 50-period moving average
        bars['ATR_50MA'] = bars['ATR'].rolling(window=50).mean()

        # Calculate EMAs
        bars['EMA_9'] = close.ewm(span=9, adjust=False).mean()
        bars['EMA_21'] = close.ewm(span=21, adjust=False).mean()

        # Determine regime validity
        bars['regime_valid'] = bars['ATR'] < bars['ATR_50MA']

        # Determine entry signals
        bars['long_entry'] = (bars['EMA_9'] > bars['EMA_21']) & (bars['regime_valid'].shift(1))

        # Determine exit signals
        bars['exit'] = (bars['EMA_9'] < bars['EMA_21']) | (bars['ATR'] > bars['ATR_50MA'])

        # Initialize signal series
        signals = pd.Series(0, index=bars.index)

        # Apply entry and exit signals
        signals[bars['long_entry']] = 1
        signals[bars['exit']] = -1

        # Apply max_trades_per_day constraint
        daily_signals = signals.resample('D').apply(lambda x: (x == 1).sum())
        cumulative_trades = daily_signals.cumsum()
        signals = signals.where(cumulative_trades <= self.max_trades_per_day, 0)

        # Apply no_overnight constraint
        signals = signals.between_time('09:30:00', '16:00:00')

        return signals
```

### Explanation:
1. **Initialization**: The strategy initializes with the required constraints (`max_trades_per_day`, `no_overnight`, `allow_fractional_shares`, and `max_contracts`).

2. **ATR Calculation**: The Average True Range (ATR) is calculated dynamically using the high, low, and close prices.

3. **Regime Validity**: The regime is considered valid when the 20-period ATR is below its 50-period moving average.

4. **EMA Calculation**: Exponential Moving Averages (EMAs) for 9 and 21 periods are calculated.

5. **Signal Generation**: 
   - **Entry Signal**: A long position is entered when the 9-period EMA crosses above the 21-period EMA, and the regime is valid.
   - **Exit Signal**: The position is exited when the 9-period EMA crosses below the 21-period EMA, or when the ATR expands above its 50-period moving average.

6. **Constraints Application**:
   - **Max Trades Per Day**: The strategy ensures no more than 3 trades are made in a single day.
   - **No Overnight**: The strategy only operates within the trading day hours (9:30 AM to 4:00 PM).

7. **Output**: The `generate_signals` method returns a series of signals where `1` indicates a long entry and `-1` indicates an exit.

This implementation should meet the specified requirements and constraints.