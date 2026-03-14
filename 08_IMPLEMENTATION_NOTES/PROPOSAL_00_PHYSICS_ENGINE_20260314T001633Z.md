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
    @abstractmethod
    def prepare_data(self, data: pd.DataFrame) -> tuple:
        pass

class VZooE3002RSIDivergence(Strategy):
    def __init__(self):
        self.max_contracts = 1
        self.no_overnight = True
        self.max_trades_per_day = 3

    def prepare_data(self, data: pd.DataFrame) -> tuple:
        # Ensure the necessary columns are present
        if not {'Close', 'RSI'}.issubset(data.columns):
            raise ValueError("Data must contain 'Close' and 'RSI' columns")

        # Calculate ATR
        data['TR1'] = abs(data['High'] - data['Low'])
        data['TR2'] = abs(data['High'] - data['Close'].shift(1))
        data['TR3'] = abs(data['Low'] - data['Close'].shift(1))
        data['TR'] = data[['TR1', 'TR2', 'TR3']].max(axis=1)
        data['ATR'] = data['TR'].rolling(window=14).mean()

        # Detect price new high
        data['PriceNewHigh'] = data['Close'] > data['Close'].rolling(window=20).max()

        # Detect RSI not confirming new high
        data['RSINotConfirming'] = (data['PriceNewHigh'] == True) & (data['RSI'] < data['RSI'].shift(1))

        # Generate entry signal
        data['entry_signal'] = data['RSINotConfirming']

        # Generate exit signal (simple for demonstration, can be expanded)
        data['exit_signal'] = data['RSI'] > 50

        # Get the latest signals and ATR
        latest_entry_signal = data['entry_signal'].iloc[-1]
        latest_exit_signal = data['exit_signal'].iloc[-1]
        latest_atr = data['ATR'].iloc[-1]

        return (latest_entry_signal, latest_exit_signal, latest_atr)
```

This code provides a blueprint for the `VZooE3002RSIDivergence` strategy, inheriting from the `Strategy` class and implementing the `prepare_data` method. It calculates the Average True Range (ATR) and detects RSI divergence from price to generate entry and exit signals. The method returns the latest entry signal, exit signal, and ATR value.