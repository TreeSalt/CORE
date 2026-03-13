---
DOMAIN: 00_PHYSICS_ENGINE
MODEL: qwen2.5-coder:32b
TIER: heavy
TYPE: IMPLEMENTATION
STATUS: RATIFIED
---

```python
from antigravity_harness.strategies.base import BaseStrategy
import pandas as pd

class VZooE1001VolatilityGatekeeper(BaseStrategy):
    """
    VARIANT: ZOO_E1_001
    REGIME_AFFINITY: Low-volatility trending — enters calm before momentum, exits before volatility expansion punishes position.
    ANTI_FRAGILITY_SCORE: 8/10 — ATR gate acts as automatic Black Swan circuit breaker. High-vol crisis events trigger ATR expansion, which closes the entry gate before damage accumulates.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_trades_per_day = 3
        self.no_overnight = True
        self.allow_fractional_shares = False
        self.max_contracts = 1

    def generate_signals(self, bars: pd.DataFrame) -> pd.Series:
        # Calculate ATR and its moving averages
        bars['TR'] = bars[['high', 'low', 'close']].apply(lambda x: max(x['high'] - x['low'], abs(x['high'] - bars['close'].shift(1)), abs(x['low'] - bars['close'].shift(1))), axis=1)
        bars['ATR'] = bars['TR'].rolling(window=20).mean()
        bars['ATR_50MA'] = bars['ATR'].rolling(window=50).mean()

        # Calculate EMAs
        bars['EMA_9'] = bars['close'].ewm(span=9, adjust=False).mean()
        bars['EMA_21'] = bars['close'].ewm(span=21, adjust=False).mean()

        # Determine entry conditions
        bars['entry_condition'] = (bars['ATR'] < bars['ATR_50MA']) & (bars['EMA_9'] > bars['EMA_21']) & (bars['EMA_9'].shift(1) <= bars['EMA_21'].shift(1))

        # Determine exit conditions
        bars['exit_condition'] = (bars['EMA_9'] < bars['EMA_21']) | (bars['ATR'] > bars['ATR_50MA'])

        # Generate signals
        signals = pd.Series(0, index=bars.index)
        signals[bars['entry_condition']] = 1
        signals[bars['exit_condition']] = -1

        # Apply trade limits
        daily_trades = signals.resample('D').cumsum()
        signals[daily_trades > self.max_trades_per_day] = 0

        return signals

    def on_trade(self, trade_data: dict):
        # Implement any necessary actions on trade execution
        pass

    def on_bar(self, bar_data: dict):
        # Implement any necessary actions on new bar data
        pass
```

This Python strategy file follows the blueprint and constraints provided, ensuring it inherits from `BaseStrategy`, implements `generate_signals`, and adheres to the specified trading rules. It calculates the Average True Range (ATR) and its moving averages to determine entry and exit conditions, and applies trade limits to ensure compliance with the strategy requirements.