---
DOMAIN: 00_PHYSICS_ENGINE
MODEL: qwen2.5-coder:32b
TIER: heavy
TYPE: IMPLEMENTATION
STATUS: RATIFIED
---

```python
from antigravity_harness.strategies.base import Strategy

class VZooE4001BollingerVWAPHybrid(Strategy):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_contracts = 1
        self.no_overnight = True
        self.max_trades_per_day = 3

    def prepare_data(self, data):
        # Calculate Bollinger Bands
        data['sma'] = data['close'].rolling(window=20).mean()
        data['std'] = data['close'].rolling(window=20).std()
        data['upper_band'] = data['sma'] + (data['std'] * 2)
        data['lower_band'] = data['sma'] - (data['std'] * 2)
        data['bandwidth'] = data['upper_band'] - data['lower_band']

        # Calculate VWAP
        data['vwap'] = (data['volume'] * ((data['high'] + data['low'] + data['close']) / 3)).cumsum() / data['volume'].cumsum()

        # Calculate Price Deviation from VWAP
        data['price_deviation'] = (data['close'] - data['vwap']) / data['vwap']

        # Calculate ATR
        data['high_low'] = data['high'] - data['low']
        data['high_close'] = (data['high'] - data['close'].shift(1)).abs()
        data['low_close'] = (data['low'] - data['close'].shift(1)).abs()
        data['tr'] = data[['high_low', 'high_close', 'low_close']].max(axis=1)
        data['atr'] = data['tr'].rolling(window=14).mean()

        # Generate Entry Signal
        data['bollinger_squeeze'] = (data['bandwidth'] < (data['bandwidth'].rolling(window=20).mean() * 0.2))
        data['price_vwap_deviation'] = (data['price_deviation'].abs() > 1.5)
        data['entry_signal'] = (data['bollinger_squeeze'] & data['price_vwap_deviation'])

        # Generate Exit Signal
        # For simplicity, let's assume exit when price crosses back over VWAP
        data['exit_signal'] = (data['close'].shift(1) > data['vwap'].shift(1)) & (data['close'] <= data['vwap'])

        # Return the last row's signals and ATR
        return (data['entry_signal'].iloc[-1], data['exit_signal'].iloc[-1], data['atr'].iloc[-1])

# Example usage:
# strategy = VZooE4001BollingerVWAPHybrid()
# entry_signal, exit_signal, atr = strategy.prepare_data(data)
```

This code defines a new strategy class `VZooE4001BollingerVWAPHybrid` that inherits from the `Strategy` base class. The `prepare_data` method calculates the necessary indicators (Bollinger Bands, VWAP, Price Deviation, and ATR) and generates entry and exit signals based on the specified conditions. The method returns the last row's entry signal, exit signal, and ATR value.