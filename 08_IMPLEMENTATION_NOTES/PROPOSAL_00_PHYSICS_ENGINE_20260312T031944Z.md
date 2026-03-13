---
DOMAIN: 00_PHYSICS_ENGINE
MODEL: qwen2.5-coder:32b
TIER: heavy
TYPE: IMPLEMENTATION
STATUS: RATIFIED
---

Certainly! Below is a proposed implementation of the `ZOO_E1_004 — OPENING_RANGE_BREAKOUT` strategy in Python, adhering to the specified constraints and requirements:

```python
from typing import Optional
import pandas as pd
from antigravity_harness.strategies.base import BaseStrategy

class ZOO_E1_004_OpeningRangeBreakout(BaseStrategy):
    """
    VARIANT: ZOO_E1_004
    REGIME_AFFINITY: High-conviction directional days — gap-and-go sessions,
                     FOMC follow-through, earnings-driven index moves.
    ANTI_FRAGILITY_SCORE: 7/10
    """
    
    def __init__(self, allow_fractional_shares=False, max_contracts=1, no_overnight=True, max_trades_per_day=3):
        super().__init__(allow_fractional_shares, max_contracts, no_overnight, max_trades_per_day)
    
    def generate_signals(self, bars: pd.DataFrame) -> pd.Series:
        """
        Generates trading signals based on the Opening Range Breakout strategy.
        
        Parameters:
        bars (pd.DataFrame): Dataframe containing OHLCV data.
        
        Returns:
        pd.Series: Series of signals (1 for long, 0 for hold, -1 for exit).
        """
        # Ensure the data has the required columns
        required_columns = ['high', 'low', 'close', 'volume']
        if not all(col in bars.columns for col in required_columns):
            raise ValueError("Input DataFrame must contain 'high', 'low', 'close', and 'volume' columns.")
        
        # Calculate the opening range (first 6 bars after market open)
        opening_range = bars.iloc[:6]
        opening_high = opening_range['high'].max()
        opening_low = opening_range['low'].min()
        opening_range_width = opening_high - opening_low
        opening_range_volume_avg = opening_range['volume'].mean()
        
        # Calculate the volume confirmation threshold
        volume_threshold = 1.5 * opening_range_volume_avg
        
        # Initialize signal series
        signals = pd.Series(0, index=bars.index)
        
        # Determine entry conditions
        entry_condition = (bars['close'] > opening_high) & (bars['volume'] > volume_threshold)
        entry_point = bars[entry_condition].index
        
        # Determine exit conditions
        exit_condition = (bars['close'] < opening_high) & (bars['close'] > opening_low)
        exit_point = bars[exit_condition].index
        
        # Determine stop loss condition
        stop_loss_condition = (bars['close'] < (opening_high - 0.5 * opening_range_width))
        stop_loss_point = bars[stop_loss_condition].index
        
        # Set signals based on conditions
        for idx in entry_point:
            signals[idx] = 1
        
        for idx in exit_point:
            if signals[idx] == 1:
                signals[idx] = -1
        
        for idx in stop_loss_point:
            if signals[idx] == 1:
                signals[idx] = -1
        
        # Ensure no overnight positions
        signals[signals.index[-1]] = -1
        
        return signals

    def __str__(self):
        return "ZOO_E1_004_OpeningRangeBreakout"
```

### Explanation:

1. **Initialization**: The strategy inherits from `BaseStrategy` and initializes with the specified constraints.
2. **Data Validation**: Ensures that the input DataFrame contains the required columns.
3. **Opening Range Calculation**: Computes the opening range using the first 6 bars.
4. **Volume Threshold**: Sets the volume threshold as 1.5 times the average volume of the opening range.
5. **Signal Generation**:
   - **Entry**: Sets a long signal when the close price is above the opening range high and the volume is above the threshold.
   - **Exit**: Sets an exit signal when the close price is back within the opening range.
   - **Stop Loss**: Sets a stop loss signal when the close price falls to 50% below the opening range high.
6. **No Overnight Positions**: Ensures that the last signal of the day is an exit.

This strategy is designed to be robust and comply with the specified constraints, ensuring it performs as intended in the Physics Engine.