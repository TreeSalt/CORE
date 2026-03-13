---
DOMAIN: 00_PHYSICS_ENGINE
MODEL: qwen2.5-coder:32b
TIER: heavy
TYPE: IMPLEMENTATION
STATUS: RATIFIED
---

```python
import pandas as pd

class ZooStrategyAdapter(Strategy):
    def __init__(self, zoo_strategy):
        self.zoo_strategy = zoo_strategy

    def prepare_data(self, df, params):
        # Step 1: Generate signals using the wrapped Zoo strategy
        signals = self.zoo_strategy.generate_signals(df)
        
        # Step 2: Convert signals to entry_signal and exit_signal
        df.loc[:, 'entry_signal'] = (signals > 0)
        df.loc[:, 'exit_signal'] = (signals < 0)
        
        # Step 3: Compute ATR using the 20-period True Range method
        df.loc[:, 'TR'] = df.loc[:, 'high'] - df.loc[:, 'low']
        df.loc[:, 'TR1'] = abs(df.loc[:, 'high'] - df.loc[:, 'close'].shift(1))
        df.loc[:, 'TR2'] = abs(df.loc[:, 'low'] - df.loc[:, 'close'].shift(1))
        df.loc[:, 'TR'] = df.loc[:, ['TR', 'TR1', 'TR2']].max(axis=1)
        df.loc[:, 'ATR'] = df.loc[:, 'TR'].rolling(window=20).mean()
        
        # Drop intermediate columns if necessary
        df.drop(columns=['TR', 'TR1', 'TR2'], inplace=True)
        
        # Step 4: Return the enriched DataFrame
        return df.loc[:, ['entry_signal', 'exit_signal', 'ATR']]
```

This code defines a `ZooStrategyAdapter` class that wraps any Zoo strategy and converts its output to match the requirements of the backtest engine. It ensures that all operations follow the specified Pandas rules and constraints.