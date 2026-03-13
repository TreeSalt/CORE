---
DOMAIN: 00_PHYSICS_ENGINE
MODEL: qwen2.5-coder:32b
TIER: heavy
TYPE: IMPLEMENTATION
STATUS: RATIFIED
---

```python
"""
VARIANT: ZOO_E1_004
REGIME_AFFINITY: High-conviction directional days — gap-and-go sessions, FOMC follow-through, earnings-driven index moves.
ANTI_FRAGILITY_SCORE: 7/10 — highly regime dependent (underperforms in directionless markets) but when it fires it fires with conviction.
"""

from antigravity_harness.strategies.base import BaseStrategy
import pandas as pd

class ZOORangeBreakoutStrategy(BaseStrategy):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.opening_range_high = None
        self.opening_range_low = None
        self.opening_range_avg_volume = None
        self.entry_price = None
        self.stop_loss = None

    def generate_signals(self, bars: pd.DataFrame) -> pd.Series:
        signals = pd.Series(0, index=bars.index)

        # Determine opening range on the first bar of the session
        if len(bars) == 1:
            self.opening_range_high = bars['high'].iloc[0]
            self.opening_range_low = bars['low'].iloc[0]
            self.opening_range_avg_volume = bars['volume'].iloc[0]
        elif len(bars) < 7:
            self.opening_range_high = max(self.opening_range_high, bars['high'].iloc[-1])
            self.opening_range_low = min(self.opening_range_low, bars['low'].iloc[-1])
            self.opening_range_avg_volume = (self.opening_range_avg_volume * (len(bars) - 1) + bars['volume'].iloc[-1]) / len(bars)
        else:
            # Check for breakout
            if bars['close'].iloc[-1] > self.opening_range_high and bars['volume'].iloc[-1] > 1.5 * self.opening_range_avg_volume:
                self.entry_price = bars['close'].iloc[-1]
                self.stop_loss = self.entry_price - 0.5 * (self.opening_range_high - self.opening_range_low)
                signals.iloc[-1] = 1

            # Check for exit conditions
            if self.entry_price is not None:
                if bars['close'].iloc[-1] <= self.opening_range_high or bars['close'].iloc[-1] <= self.stop_loss:
                    signals.iloc[-1] = -1
                    self.entry_price = None
                    self.stop_loss = None

        return signals
```

### Explanation:
1. **Initialization**: The strategy initializes necessary variables for the opening range and entry conditions.
2. **Opening Range Calculation**: For the first 6 bars, it calculates the high, low, and average volume.
3. **Breakout Condition**: Starting from the 7th bar, it checks if the close price is above the opening range high and if the volume is 1.5x greater than the average volume of the opening range.
4. **Entry and Exit Conditions**: Upon a breakout, it sets the entry price and calculates the stop loss at 50% below the entry price. It exits if the price falls back within the opening range or hits the stop loss.
5. **Signal Generation**: The strategy returns a pandas Series with signals to enter (1) or exit (-1) the market.

This code should be placed in the specified file:
`antigravity_harness/strategies/lab/v_zoo_E1_004_opening_range_breakout/v_zoo_E1_004_opening_range_breakout.py`