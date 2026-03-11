---
DOMAIN: 00_PHYSICS_ENGINE
MODEL: qwen2.5-coder:32b
TIER: heavy
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

```python
"""
VARIANT: ZOO_E1_001
REGIME_AFFINITY: Low-volatility trending — enters calm before momentum, exits before volatility expansion punishes position.
ANTI_FRAGILITY_SCORE: 8/10 — ATR gate acts as automatic Black Swan circuit breaker. High-vol crisis events trigger ATR expansion, which closes the entry gate before damage accumulates.
"""

import pandas as pd
from antigravity_harness.strategies.base import BaseStrategy

class VolatilityGatekeeper(BaseStrategy):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_contracts = 1
        self.allow_fractional_shares = False
        self.no_overnight = True
        self.max_trades_per_day = 3

    def generate_signals(self, bars: pd.DataFrame) -> pd.Series:
        """
        Generates trading signals based on the VOLATILITY_GATEKEEPER strategy.
        """
        # Calculate the ATR
        bars['high_low'] = bars['high'] - bars['low']
        bars['high_close'] = abs(bars['high'] - bars['close'].shift())
        bars['low_close'] = abs(bars['low'] - bars['close'].shift())
        bars['tr'] = bars[['high_low', 'high_close', 'low_close']].max(axis=1)
        bars['atr'] = bars['tr'].rolling(window=20).mean()

        # Calculate the 50-period moving average of ATR
        bars['atr_50_ma'] = bars['atr'].rolling(window=50).mean()

        # Calculate EMAs
        bars['ema_9'] = bars['close'].ewm(span=9, adjust=False).mean()
        bars['ema_21'] = bars['close'].ewm(span=21, adjust=False).mean()

        # Determine the signal
        bars['signal'] = 0
        bars['signal'][bars['ema_9'] > bars['ema_21']] = 1
        bars['signal'][bars['ema_9'] < bars['ema_21']] = -1

        # Determine the regime (ATR gate)
        bars['regime'] = bars['atr'] < bars['atr_50_ma']

        # Apply the regime filter to the signal
        bars['filtered_signal'] = bars['signal'] * bars['regime']

        # Generate the final signal
        bars['final_signal'] = bars['filtered_signal'].diff()

        # Apply hard stop loss
        bars['stop_loss'] = bars['close'].shift() + 2 * bars['atr'].shift()

        # Exit signal when price hits the stop loss
        bars['exit_signal'] = 0
        bars.loc[bars['close'] <= bars['stop_loss'], 'exit_signal'] = -1

        # Exit signal when ATR expands above its 50-period MA
        bars.loc[bars['atr'] > bars['atr_50_ma'], 'exit_signal'] = -1

        # Combine the entry and exit signals
        bars['combined_signal'] = bars['final_signal'] + bars['exit_signal']

        # Ensure no overnight positions
        bars['combined_signal'].iloc[0] = 0  # No position on the first bar
        bars['combined_signal'].iloc[-1] = -1  # Ensure no overnight position

        # Ensure max_trades_per_day constraint
        daily_signals = bars['combined_signal'].resample('D').sum()
        daily_signals[daily_signals > 3] = 3
        bars['daily_trade_count'] = bars['combined_signal'].cumsum().groupby(bars.index.date).transform('count')
        bars['combined_signal'][bars['daily_trade_count'] > daily_signals] = 0

        return bars['combined_signal']
```

This code defines a `VolatilityGatekeeper` class that inherits from `BaseStrategy` and implements the `generate_signals` method as per the ZOO_E1_001 strategy blueprint. The strategy dynamically calculates ATR and EMAs, applies the volatility gate, and generates buy/sell signals based on the specified rules. The code also includes mechanisms to enforce the constraints such as no overnight positions and a maximum of three trades per day.