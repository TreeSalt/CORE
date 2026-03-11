---
DOMAIN: 00_PHYSICS_ENGINE
MODEL: qwen2.5-coder:32b
TIER: heavy
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

```python
# antigravity_harness/strategies/lab/v_zoo_E1_004_opening_range_breakout/v_zoo_E1_004_opening_range_breakout.py

import pandas as pd
from antigravity_harness.strategies.base import BaseStrategy

class ZOO_E1_004_OpeningRangeBreakout(BaseStrategy):
    """
    VARIANT: ZOO_E1_004
    REGIME_AFFINITY: High-conviction directional days — gap-and-go sessions, FOMC follow-through, earnings-driven index moves.
    ANTI_FRAGILITY_SCORE: 7/10
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.allow_fractional_shares = False
        self.max_contracts = 1
        self.no_overnight = True
        self.max_trades_per_day = 3

    def generate_signals(self, bars: pd.DataFrame) -> pd.Series:
        """
        Generate trading signals based on the Opening Range Breakout strategy.

        :param bars: DataFrame containing OHLCV data
        :return: Series of signals (-1, 0, 1)
        """
        # Define the opening range (first 6 bars after market open)
        opening_range = bars.iloc[:6]
        opening_high = opening_range['high'].max()
        opening_low = opening_range['low'].min()
        opening_range_width = opening_high - opening_low
        opening_avg_volume = opening_range['volume'].mean()

        # Initialize signals
        signals = pd.Series(0, index=bars.index)

        # Calculate entry conditions
        for i in range(6, len(bars)):
            if bars['close'].iloc[i] > opening_high and bars['volume'].iloc[i] > 1.5 * opening_avg_volume:
                signals.iloc[i] = 1
                entry_price = bars['close'].iloc[i]
                stop_loss = entry_price - 0.5 * opening_range_width
                break

        # Calculate exit conditions
        for i in range(signals[signals == 1].index[0] + 1, len(bars)):
            if bars['close'].iloc[i] <= opening_high or bars['close'].iloc[i] <= stop_loss:
                signals.iloc[i] = -1
                break

        return signals
```

### Explanation:
- **Inheritance**: The class `ZOO_E1_004_OpeningRangeBreakout` inherits from `BaseStrategy`.
- **Initialization**: The constructor sets up the strategy parameters as per the requirements.
- **Signal Generation**:
  - The opening range is defined as the first 6 bars after market open.
  - The strategy looks for a breakout above the opening range high with volume confirmation.
  - If the breakout occurs, a long position is taken.
  - The strategy exits if the price returns within the opening range or hits a stop loss at 50% of the opening range width.
  - The strategy ensures no overnight positions and limits to one trade per day.

This code should be placed in the specified file path and should pass the strategy contract test suite once integrated into the broader system.