---
DOMAIN: 00_PHYSICS_ENGINE
MODEL: qwen2.5-coder:32b
TIER: heavy
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

```python
from antigravity_harness.strategies.base import BaseStrategy
import pandas as pd

class VZooE1005MomentumDecayHarvester(BaseStrategy):
    """
    VARIANT: ZOO_E1_005
    REGIME_AFFINITY: Any regime with intraday momentum spikes — works in both trending and volatile environments.
    ANTI_FRAGILITY_SCORE: 8/10
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_trades_per_day = 3
        self.max_contracts = 1
        self.no_overnight = True
        self.allow_fractional_shares = False

    def generate_signals(self, bars: pd.DataFrame) -> pd.Series:
        """
        Generates trading signals based on the MOMENTUM_DECAY_HARVESTER strategy.
        :param bars: DataFrame containing historical price data.
        :return: Series of trading signals (1 for long entry, -1 for exit, 0 for hold).
        """
        # Calculate percentage change for each 5m bar
        bars['pct_change'] = bars['close'].pct_change()
        
        # Identify bars where the price has moved up >0.3% in a single 5m bar (momentum spike)
        bars['momentum_spike'] = bars['pct_change'] > 0.003
        
        # Determine the range of the spike bar
        bars['spike_high'] = bars['high'].where(bars['momentum_spike'])
        bars['spike_low'] = bars['low'].where(bars['momentum_spike'])
        
        # Identify the following bar that opens inside the spike bar's range (consolidation signal)
        bars['consolidation_open'] = bars['open'].shift(-1)
        bars['consolidation_high'] = bars['high'].shift(-1)
        bars['consolidation_low'] = bars['low'].shift(-1)
        
        bars['consolidation_signal'] = (
            bars['consolidation_open'] >= bars['spike_low'] &
            bars['consolidation_open'] <= bars['spike_high']
        )
        
        # Define entry condition: momentum spike followed by a consolidation bar
        bars['entry_condition'] = bars['momentum_spike'] & bars['consolidation_signal'].shift(-1)
        
        # Define exit condition: price falls below the low of the consolidation bar
        bars['exit_condition'] = bars['low'] <= bars['consolidation_low'].shift(-1)
        
        # Generate signals
        bars['signal'] = 0
        bars.loc[bars['entry_condition'], 'signal'] = 1
        bars.loc[bars['exit_condition'], 'signal'] = -1
        
        # Ensure no overnight positions
        bars['signal'].where(bars.index.hour < 16, 0, inplace=True)
        
        # Cap the number of trades per day
        daily_trades = bars['signal'].groupby(bars.index.date).cumsum()
        bars['signal'].where(daily_trades <= self.max_trades_per_day, 0, inplace=True)
        
        return bars['signal']
```

This code provides a strategy class `VZooE1005MomentumDecayHarvester` that inherits from `BaseStrategy` and implements the `generate_signals` method according to the provided blueprint and constraints. The strategy identifies entry points based on a momentum spike followed by a consolidation bar and exits when the price falls below the low of the consolidation bar. It also ensures no overnight positions and caps the number of trades per day to three.