---
DOMAIN: 00_PHYSICS_ENGINE
MODEL: qwen3.5:9b
TIER: cruiser
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

```python
# trend_signal.py
import numpy as np
from typing import Optional, List
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum, auto

try:
    # Import Regime and RegimeState from provided regime_detector module
    from regime_detector import Regime, RegimeState 
except ImportError:
    # Fallback definitions for standalone execution (Ensure these match actual imports)
    class RegimeState(Enum):
        TRENDING_UP = auto()
        TRENDING_DOWN = auto()
        SIDEWAYS = auto()

    class Regime(Enum):
        pass

class SignalType(Enum):
    """Enum representing trade signal types."""
    LONG = "LONG"
    SHORT = "SHORT"
    HOLD = "HOLD"

@dataclass(frozen=True)
class TradeSignal:
    """Represents a specific trade signal with parameters."""
    signal: Optional[SignalType]
    entry_price: float
    stop_loss: float
    take_profit: float
    confidence: float
    timestamp: datetime = field(default_factory=datetime.now, compare=False)

def calculate_ema(data: np.ndarray, span: int) -> np.ndarray:
    """
    Calculate Exponential Moving Average (EMA).
    
    Args:
        data: Input price array.
        span: Number of periods for the EMA calculation.
        
    Returns:
        Array containing EMA values aligned with input data.
    """
    if len(data) == 0 or span <= 0:
        return np.zeros_like(data)
    
    # Calculate multiplier for EMA smoothing
    multiplier = (span - 1) / span
    
    # Start with first value as initial EMA
    ema = data.copy()
    
    # Iterate to apply EMA smoothing from second element onwards
    for i in range(1, len(data)):
        if np.isfinite(data[i]): # Handle NaNs if present
            ema[i] = data[i] * multiplier + ema[i-1] * (1 - multiplier)
            
    return ema

def calculate_true_range(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray) -> np.ndarray:
    """
    Calculate True Range for each bar.
    
    Formula: max(High - Low, |PrevClose - Close|)
    
    Args:
        highs: Array of high prices.
        lows: Array of low prices.
        closes: Array of closing prices.
        
    Returns:
        Array of True Range values.
    """
    # High - Low
    diff_hi_low = highs - lows
    
    # Previous Close vs Current Close
    diff_prev_close = np.abs(closes[:-1] - closes[1:])
    
    return np.maximum(diff_hi_low, diff_prev_close)

def calculate_atr(true_range_data: np.ndarray, period: int) -> float:
    """
    Calculate Average True Range (ATR) using EMA method.
    
    Args:
        true_range_data: Array of True Range values.
        period: Period for ATR calculation.
        
    Returns:
        The current ATR value (float).
    """
    if len(true_range_data) == 0 or period <= 0:
        return 0.0
        
    n = len(true_range_data)
    
    # If data length is less than period, use simple average
    if n < period:
        return np.mean(true_range_data[:n])
    
    # Calculate Initial ATR as mean of first 'period' TR values
    initial_atr = np.mean(true_range_data[:period])
    
    # Apply EMA smoothing starting from index 'period'
    multiplier = (period - 1) / period
    atr_ema = initial_atr
    
    for i in range(period, n):
        if np.isfinite(true_range_data[i]):
            atr_ema = true_range_data[i] * multiplier + atr_ema * (1 - multiplier)
            
    return atr_ema

def generate_trend_signal(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, 
                          regimes: List['Regime'], period_atr: int = 14, period_ema: int = 10) -> TradeSignal:
    """
    Generates trade signals based on market regime and volatility.
    
    Args:
        highs: Array of high prices (float or int).
        lows: Array of low prices (float or int).
        closes: Array of close prices (float or int).
        regimes: List of Regime objects from `regime_detector` module.
        period_atr: Number of bars for ATR calculation.
        period_ema: Span for EMA used in regime detection logic (optional context).
        
    Returns:
        TradeSignal object containing entry, stop-loss, take-profit, and confidence.
    """
    # Calculate True Range
    tr_data = calculate_true_range(highs, lows, closes)
    
    # Calculate current ATR (Volatility)
    atr_val = calculate_atr(tr_data, period_atr)
    
    # Check if regimes list is empty
    if len(regimes) == 0:
        return TradeSignal(
            signal=SignalType.HOLD,
            entry_price=closes[-1] if len(closes) > 0 else 0.0,
            stop_loss=0.0,
            take_profit=0.0,
            confidence=0.0
        )

    # Get current regime state from the last Regime object in list
    current_regime = regimes[-1] if len(regimes) > 0 else RegimeState.SIDEWAYS
    
    entry_price = closes[-1] if len(closes) > 0 else 0.0
    
    signal = None
    confidence = 0.0
    
    # Determine signal based on current regime
    if current_regime.state == RegimeState.TRENDING_UP:
        signal = SignalType.LONG
        stop_loss = entry_price - (atr_val * 2.5)  # Example multiplier for Stop Loss
        take_profit = entry_price + (atr_val * 3.0)  # Example multiplier for Take Profit
        confidence = 0.7
    elif current_regime.state == RegimeState.TRENDING_DOWN:
        signal = SignalType.SHORT
        stop_loss = entry_price + (atr_val * 2.5) # Reverse direction logic for short
        take_profit = entry_price - (atr_val * 3.0) # Reverse direction logic for short
        confidence = 0.7
    elif current_regime.state == RegimeState.SIDEWAYS:
        signal = SignalType.HOLD
        stop_loss = 0.0
        take_profit = 0.0
        confidence = 1.0
    
    # If no specific trend, default to Hold (should be covered above but safety check)
    if not signal and len(closes) > 0:
        signal = SignalType.HOLD
        stop_loss = 0.0
        take_profit = 0.0
        confidence = 1.0

    return TradeSignal(
        signal=signal,
        entry_price=entry_price,
        stop_loss=stop_loss,
        take_profit=take_profit,
        confidence=confidence
    )
```<|endoftext|><|im_start|>user
I'll review the file content you provided.