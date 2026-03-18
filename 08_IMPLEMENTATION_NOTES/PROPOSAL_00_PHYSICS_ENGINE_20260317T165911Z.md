---
DOMAIN: 00_PHYSICS_ENGINE
MODEL: qwen2.5-coder:32b
TIER: heavy
TYPE: IMPLEMENTATION
STATUS: RATIFIED
---

```python
import json
import math
import statistics
from dataclasses import dataclass
from typing import List, Optional
from enum import Enum
from pathlib import Path
from datetime import datetime

# Define Signal Enum
class Signal(Enum):
    BUY = 1
    SELL = 2
    HOLD = 3
    STOP_LOSS = 4

# Define TradeLog Dataclass
@dataclass
class TradeLog:
    entry_price: Optional[float] = None
    exit_price: Optional[float] = None
    entry_time: Optional[datetime] = None
    exit_time: Optional[datetime] = None
    pnl: Optional[float] = None
    trades: List = []

# Rolling mean calculation
def rolling_mean(prices: List[float], window: int) -> List[float]:
    if window <= 0:
        raise ValueError("Window must be positive")
    rolling_means = []
    for i in range(len(prices) - window + 1):
        window_prices = prices[i:i + window]
        rolling_means.append(statistics.mean(window_prices))
    return rolling_means

# Rolling standard deviation calculation
def rolling_std(prices: List[float], window: int) -> List[float]:
    if window <= 0:
        raise ValueError("Window must be positive")
    rolling_stds = []
    for i in range(len(prices) - window + 1):
        window_prices = prices[i:i + window]
        rolling_stds.append(statistics.stdev(window_prices))
    return rolling_stds

# Z-score calculation
def compute_zscore(price: float, mean: float, std: float) -> float:
    if std == 0:
        raise ValueError("Standard deviation must not be zero")
    return (price - mean) / std

# Signal generation based on z-score
def generate_signals(prices: List[float], window: int, entry_z: float, exit_z: float, stop_z: float) -> List[Signal]:
    if len(prices) < window:
        raise ValueError("Prices list must be longer than window size")
    
    means = rolling_mean(prices, window)
    stds = rolling_std(prices, window)
    signals = []
    
    for i in range(window, len(prices)):
        z_score = compute_zscore(prices[i], means[i - window], stds[i - window])
        if z_score < stop_z:
            signals.append(Signal.STOP_LOSS)
        elif z_score < entry_z:
            signals.append(Signal.BUY)
        elif z_score > exit_z:
            signals.append(Signal.SELL)
        else:
            signals.append(Signal.HOLD)
    
    return signals

# Trade tracking and P&L calculation
def track_trades(signals: List[Signal], prices: List[float], max_position: int = 1, stop_loss: float = -3.0) -> TradeLog:
    trade_log = TradeLog()
    in_trade = False
    entry_price = None
    entry_time = None
    
    for i in range(len(signals)):
        if signals[i] == Signal.BUY and not in_trade:
            if entry_price is None:
                entry_price = prices[i]
                entry_time = datetime.now()
                in_trade = True
                trade_log.trades.append({"action": "BUY", "price": entry_price, "time": entry_time})
        elif signals[i] == Signal.SELL and in_trade:
            exit_price = prices[i]
            exit_time = datetime.now()
            in_trade = False
            pnl = exit_price - entry_price
            trade_log.entry_price = entry_price
            trade_log.exit_price = exit_price
            trade_log.entry_time = entry_time
            trade_log.exit_time = exit_time
            trade_log.pnl = pnl
            trade_log.trades.append({"action": "SELL", "price": exit_price, "time": exit_time, "pnl": pnl})
        elif signals[i] == Signal.STOP_LOSS and in_trade:
            exit_price = prices[i]
            exit_time = datetime.now()
            in_trade = False
            pnl = exit_price - entry_price
            trade_log.entry_price = entry_price
            trade_log.exit_price = exit_price
            trade_log.entry_time = entry_time
            trade_log.exit_time = exit_time
            trade_log.pnl = pnl
            trade_log.trades.append({"action": "STOP_LOSS", "price": exit_price, "time": exit_time, "pnl": pnl})
    
    return trade_log

# Example usage for testing
if __name__ == "__main__":
    synthetic_prices = [100, 95, 90, 85, 80, 75, 70, 75, 80, 85, 90, 95, 100, 105, 110, 115, 120, 125, 120, 115, 110, 105, 100, 95, 90, 85, 80, 75, 70, 75, 80, 85, 90, 95, 100]
    window = 10
    entry_z = -2.0
    exit_z = 2.0
    stop_z = -3.0
    
    signals = generate_signals(synthetic_prices, window, entry_z, exit_z, stop_z)
    trade_log = track_trades(signals, synthetic_prices)
    
    print("Signals:", [signal.name for signal in signals])
    print("Trade Log:", trade_log.trades)
```

This code defines a mean reversion strategy based on z-score deviation from a rolling mean, including the required functions and data structures. It ensures that the strategy handles BUY, SELL, HOLD, and STOP_LOSS signals according to the specified conditions and tracks trades with P&L calculations. The example usage at the end demonstrates how to test the strategy with a synthetic price series.