---
DOMAIN: 00_PHYSICS_ENGINE
MODEL: qwen2.5-coder:32b
TIER: heavy
TYPE: IMPLEMENTATION
STATUS: RATIFIED
---

```python
from abc import ABC, abstractmethod
import pandas as pd

class Strategy(ABC):
    def __init__(self, data):
        self.data = data

    @abstractmethod
    def prepare_data(self):
        pass

class VZooE3003MarketProfileValue(Strategy):
    def __init__(self, data):
        super().__init__(data)

    def prepare_data(self):
        # Calculate ATR
        high = self.data.loc[:, 'high']
        low = self.data.loc[:, 'low']
        close = self.data.loc[:, 'close']
        
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = true_range.rolling(window=14).mean()
        
        # Identify Point of Control (POC) from the prior session
        poc = self.data.loc[self.data.index[-2], 'close']
        
        # Current price
        current_price = self.data.loc[self.data.index[-1], 'close']
        
        # Determine entry and exit signals
        deviation = abs(current_price - poc)
        entry_signal = (deviation > atr.iloc[-1])
        exit_signal = (deviation <= atr.iloc[-1])
        
        return entry_signal, exit_signal, atr.iloc[-1]
```

This code defines a strategy class `VZooE3003MarketProfileValue` that inherits from the `Strategy` abstract base class. It implements the `prepare_data` method to calculate the Average True Range (ATR), identify the Point of Control (POC) from the prior session, and determine entry and exit signals based on the given criteria. The method returns the entry signal, exit signal, and the latest ATR value.