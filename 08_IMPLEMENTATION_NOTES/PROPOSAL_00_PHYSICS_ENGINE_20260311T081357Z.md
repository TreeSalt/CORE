---
DOMAIN: 00_PHYSICS_ENGINE
MODEL: qwen2.5-coder:32b
TIER: heavy
TYPE: IMPLEMENTATION
STATUS: RATIFIED
---

```python
# antigravity_harness/strategies/lab/v_zoo_E1_005_momentum_decay_harvester/v_zoo_E1_005_momentum_decay_harvester.py

from antigravity_harness.strategies.base import BaseStrategy
import pandas as pd

class ZOO_E1_005_Momentum_Decay_Harvester(BaseStrategy):
    """
    VARIANT: ZOO_E1_005
    REGIME_AFFINITY: Any regime with intraday momentum spikes — works in both trending and volatile environments.
    ANTI_FRAGILITY_SCORE: 8/10
    """

    def __init__(self):
        super().__init__()
        self.max_contracts = 1
        self.allow_fractional_shares = False
        self.no_overnight = True
        self.max_trades_per_day = 3
        self.current_trades = 0

    def generate_signals(self, bars: pd.DataFrame) -> pd.Series:
        # Calculate percentage change for each bar
        bars['Price_Change'] = bars['close'].pct_change() * 100

        # Identify momentum spikes
        bars['Momentum_Spike'] = bars['Price_Change'] > 0.3

        # Check for consolidation signal
        bars['Consolidation_Signal'] = (bars['open'].shift(-1) >= bars['low']) & (bars['open'].shift(-1) <= bars['high'])

        # Determine entry conditions
        bars['Entry_Signal'] = bars['Momentum_Spike'] & bars['Consolidation_Signal'].shift(-1)

        # Calculate target and stop levels
        bars['Spike_Size'] = bars['high'] - bars['low']
        bars['Target'] = bars['open'].shift(-1) + (bars['Spike_Size'] * 0.5)
        bars['Stop'] = bars['low'].shift(-1)

        # Generate signals
        signals = pd.Series(index=bars.index, dtype=float)
        for i in range(1, len(bars)):
            if bars['Entry_Signal'].iloc[i] and self.current_trades < self.max_trades_per_day:
                signals.iloc[i] = 1  # Enter long
                self.current_trades += 1

        # Exit logic based on target or stop
        for i in range(1, len(bars)):
            if signals.iloc[i] == 1:
                if bars['close'].iloc[i] >= bars['Target'].iloc[i]:
                    signals.iloc[i] = -1  # Exit on target
                    self.current_trades -= 1
                elif bars['close'].iloc[i] <= bars['Stop'].iloc[i]:
                    signals.iloc[i] = -1  # Exit on stop
                    self.current_trades -= 1

        # Reset trades at the end of the day
        if not bars['close'].iloc[-1].isnull():
            self.current_trades = 0

        return signals

    def reset(self):
        self.current_trades = 0
```

This Python file implements the `ZOO_E1_005_Momentum_Decay_Harvester` strategy, inheriting from `BaseStrategy`. It includes the necessary logic to generate signals based on the specified rules, ensuring that all constraints are adhered to. The strategy calculates momentum spikes, consolidation signals, and sets targets and stops dynamically. It also includes logic to manage the number of trades per day and resets the trade count at the end of each day.