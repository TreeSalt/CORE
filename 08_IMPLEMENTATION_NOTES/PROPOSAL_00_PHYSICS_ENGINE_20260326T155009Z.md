---
DOMAIN: 00_PHYSICS_ENGINE
MODEL: qwen3.5:9b
TIER: cruiser
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

```python
from typing import Optional
import math


class Strategy:
    pass


class ATRRegimeStrategy(Strategy):
    def __init__(self, config):
        self.atr_period = config['atr_period']
        self.regime_lookback = config['regime_lookback']
        self.trend_threshold = config['trend_threshold']
        
        # Internal state variables
        self.current_atr = 0.0
        self.atr_history = []
        self.recent_regimes = []
        self.volume_ma: float = 0.0
        
    def _calculate_atr(self, candle):
        if not candle.get('atr'):
            return self.current_atr
        
        self.current_atr = candle['atr']
        self.atr_history.append(self.current_atr)
        
        if len(self.atr_history) > self.atr_period:
            self.atr_history.pop(0)
            
        # Update moving average of ATR
        if len(self.atr_history) == 1:
            self.volume_ma = self.current_atr
        else:
            self.volume_ma = sum(self.atr_history) / len(self.atr_history)
            
    def _detect_regime(self, candle):
        if not candle.get('returns'):
            return 'neutral'
            
        recent_returns = []
        for i in range(1, min(candle.get('returns', 0), self.regime_lookback)):
            if candle['returns'] - candle.get('prev_retreats', {}).get(i, 0) != 0:
                continue
            recent_returns.append(abs(candle['returns']))
        
        avg_return = sum(recent_returns) / len(recent_returns) if recent_returns else 0
        
        return 'trending' if abs(avg_return) >= self.trend_threshold else 'neutral'
    
    def on_bar(self, candle):
        # Calculate ATR
        if self.atr_period:
            self._calculate_atr(candle)
            
        # Detect regime
        current_regime = self._detect_regime(candle)
        self.recent_regimes.append(current_regime)
        
        # Remove old regimes
        if len(self.recent_regimes) > self.regime_lookback:
            self.recent_regimes.pop(0)
            
        # Update regime count
        self.trending_count = sum(1 for r in self.recent_regimes if r == 'trending')
        
    def get_signal(self):
        # Check if we're in a trending regime
        is_in_trend = self.trending_count >= len(self.recent_regimes) * 0.5
        
        # Check volatility filter
        vol_filter_passed = False
        if self.volume_ma > 0 and self.current_atr <= 2 * self.volume_ma:
            vol_filter_passed = True
            
        if not is_in_trend or not vol_filter_passed:
            return 0.0
            
        # Generate signal based on price movement
        if candle.get('close') and candle.get('prev_close'):
            direction = 1 if candle['close'] > candle['prev_close'] else -1
            magnitude = abs((candle['close'] - candle['prev_close']) / candle['prev_close'])
            
            return min(max(direction * magnitude, -1.0), 1.0)
            
        return 0.0
```