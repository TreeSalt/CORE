---
DOMAIN: 00_PHYSICS_ENGINE
MODEL: qwen3.5:27b
TIER: heavy
TYPE: IMPLEMENTATION
STATUS: REJECTED_OBSOLETE
REJECTION_REASON: regime_detector — wrong class name (RegimeAnalyzer), wrong method name
REJECTED_AT: 2026-04-08T02:42:12.366204+00:00
---

import numpy as np
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from typing import List, Union

# --- Enums and Data Classes ---

class Regime(Enum):
    TRENDING_UP = "TRENDING_UP"
    TRENDING_DOWN = "TRENDING_DOWN"
    RANGING = "RANGING"
    VOLATILE = "VOLATILE"
    UNKNOWN = "UNKNOWN"

@dataclass
class RegimeState:
    regime: Regime
    confidence: float
    adx: float
    atr: float
    atr_ratio: float
    timestamp: datetime

# --- Indicator Math Helpers (From Scratch) ---

def _validate_input(data):
    """Ensure input is a numpy array of floats with sufficient length."""
    if not isinstance(data, np.ndarray):
        data = np.array(data, dtype=np.float64)
    
    if data.ndim != 1:
        raise ValueError("Input data must be 1-dimensional arrays.")
        
    return data

def _wilder_rma(values: np.ndarray, period: int) -> np.ndarray:
    """
    Implements Wilder's Smoothing (RMA).
    Alpha = 1 / period.
    First value is the simple moving average of the first 'period' values.
    """
    rma = np.zeros_like(values)
    
    # Initialize with SMA
    if len(values) >= period:
        initial_sma = np.nancumsum(values[:period]) / period
        rma[period-1] = initial_sma
    
    # Iterate for RMA
    alpha = 1.0 / period
    for i in range(period, len(values)):
        if not np.isnan(rma[i-1]):
            rma[i] = (values[i] - rma[i-1]) * alpha + rma[i-1]
            
    return rma

def _calculate_sma(data: np.ndarray, period: int) -> np.ndarray:
    """Standard Simple Moving Average using cumulative sum optimization."""
    sma = np.convolve(data, np.ones(period)/period, mode='valid')
    # Pad to match original length (NaN for insufficient history)
    padded_zeros = np.zeros(len(data) - len(sma))
    return np.concatenate([padded_zeros, sma])

def _calculate_std(data: np.ndarray, period: int) -> np.ndarray:
    """Standard Deviation."""
    # Using numpy rolling window logic via stride tricks or conv
    # Simple convolution approach for speed without external libs
    mean = _calculate_sma(data, period)
    
    # Calculate variance: E[X^2] - (E[X])^2
    # However, to handle NaNs correctly at the start, we use explicit slicing if possible.
    # For simplicity in this core module, we use a loop or vectorized subtraction on window.
    
    std_arr = np.zeros_like(data)
    
    for i in range(period - 1, len(data)):
        window = data[i - period + 1:i + 1]
        if not np.isnan(window).any():
            std_arr[i] = np.std(window, ddof=0) # Population std often used in TA
            
    return std_arr

def _calculate_tr(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray) -> np.ndarray:
    """Calculate True Range."""
    # TR = Max(H-L, Abs(H-C_prev), Abs(L-C_prev))
    
    # Lagged close
    c_lag = np.roll(closes, 1)
    c_lag[0] = closes[0] # Or NaN, but roll preserves array shape
    
    tr_hl = highs - lows
    tr_hc = np.abs(highs - c_lag)
    tr_lc = np.abs(lows - c_lag)
    
    true_range = np.maximum.reduce([tr_hl, tr_hc, tr_lc])
    
    # First TR is invalid (needs previous close), set to 0 or NaN logic handles it in RMA init
    return true_range

def _calculate_atr(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, period: int = 14) -> np.ndarray:
    """Calculate Average True Range using Wilder's Smoothing."""
    tr = _calculate_tr(highs, lows, closes)
    return _wilder_rma(tr, period)

def _calculate_dm_di_highs_lows_closes(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, period: int = 14):
    """
    Calculate +DM, -DM, +DI, -DI, DX, ADX.
    Returns arrays of (+DI, -DI, ADX).
    """
    
    # Lagged series
    hl = highs - lows
    
    h_lag = np.roll(highs, 1)
    l_lag = np.roll(lows, 1)
    
    raw_up_move = highs - h_lag
    raw_down_move = l_lag - lows
    
    # DM Logic
    plus_dm = np.where((raw_up_move > raw_down_move) & (raw_up_move > 0), raw_up_move, 0.0)
    minus_dm = np.where((raw_down_move > raw_up_move) & (raw_down_move > 0), raw_down_move, 0.0)
    
    # Smooth DMs using Wilder's RMA
    plus_dmr = _wilder_rma(plus_dm, period)
    minus_dmr = _wilder_rma(minus_dm, period)
    
    # Smooth ATR (needed for DI calculation)
    atr_arr = _calculate_atr(highs, lows, closes, period)
    
    # DI Calculation: DM / ATR * 100
    plus_di = np.divide(plus_dmr, atr_arr, out=np.zeros_like(atr_arr), where=atr_arr!=0) * 100
    minus_di = np.divide(minus_dmr, atr_arr, out=np.zeros_like(atr_arr), where=atr_arr!=0) * 100
    
    # DX Calculation: |+DI - -DI| / (+DI + -DI) * 100
    dx_num = np.abs(plus_di - minus_di)
    dx_denom = plus_di + minus_di
    dx = np.divide(dx_num, dx_denom, out=np.zeros_like(dx_num), where=dx_denom!=0) * 100
    
    # ADX Calculation: RMA of DX
    adx_arr = _wilder_rma(dx, period)
    
    return plus_di, minus_di, adx_arr

def _calculate_ema(data: np.ndarray, period: int) -> np.ndarray:
    """
    Calculate EMA. 
    Alpha = 2 / (period + 1).
    Initialize first value as SMA for better stability.
    """
    ema = np.zeros_like(data)
    
    # Init with SMA of first 'period' elements
    if len(data) >= period:
        ema[period-1] = np.mean(data[:period])
        
    alpha = 2 / (period + 1)
    
    for i in range(period, len(data)):
        ema[i] = data[i] * alpha + ema[i-1] * (1 - alpha)
        
    return ema

# --- Core Classifiers ---

class RegimeAnalyzer:
    def __init__(self):
        self.highs = None
        self.lows = None
        self.closes = None
        
    def analyze_regime(self, highs, lows, closes):
        """
        Main entry point. Takes raw data lists/arrays.
        Returns RegimeState object with confidence score [0.0 - 1.0].
        """
        
        # Pre-processing
        self.highs = _validate_input(highs)
        self.lows = _validate_input(lows)
        self.closes = _validate_input(closes)
        
        length = len(self.closes)
        
        # Ensure we have enough data for max period required (ATR 14, BB 20, EMA 50)
        MIN_LENGTH = 60 
        if length < MIN_LENGTH:
            return self._return_unknown_state("Insufficient data")

        # Calculate Technicals
        
        # 1. ATR (14)
        atr_14 = _calculate_atr(self.highs, self.lows, self.closes, period=14)
        
        # 2. ADX / DI (14)
        plus_di, minus_di, adx_14 = _calculate_dm_di_highs_lows_closes(
            self.highs, self.lows, self.closes, period=14
        )
        
        # 3. Bollinger Bands (20)
        close_arr = self.closes
        mid_20 = _calculate_sma(close_arr, 20)
        std_20 = _calculate_std(close_arr, 20)
        upper_bb = mid_20 + (2 * std_20)
        lower_bb = mid_20 - (2 * std_20)
        bb_width = upper_bb - lower_bb
        
        # 4. Trending EMA (50)
        ema_50 = _calculate_ema(close_arr, 50)
        
        # Current values (last index)
        curr_idx = length - 1
        curr_atr = atr_14[curr_idx]
        prev_atr = atr_14[curr_idx-1] if curr_idx > 0 else 0
        
        curr_adx = adx_14[curr_idx]
        curr_plus_di = plus_di[curr_idx]
        curr_minus_di = minus_di[curr_idx]
        
        curr_bb_width = bb_width[curr_idx]
        prev_bb_width = bb_width[curr_idx-1] if curr_idx > 0 else curr_bb_width
        
        curr_ema_50 = ema_50[curr_idx]
        curr_close = close_arr[curr_idx]
        
        # Calculate Volatility Ratio (ATR vs ATR SMA)
        atr_sma_50 = _calculate_sma(atr_14, 50)[curr_idx]
        atr_ratio = 0.0
        if not np.isnan(atr_sma_50) and atr_sma_50 > 0:
            atr_ratio = curr_atr / atr_sma_50
            
        # --- Classification Logic ---

        confidence_score = 0.5 # Baseline
        
        regime_determined = Regime.UNKNOWN
        
        # Priority 1: Volatile (High Risk)
        # If current ATR is > 2x average ATR, volatility is dominant signal regardless of trend direction
        if atr_ratio >= 2.0:
            regime_determined = Regime.VOLATILE
            confidence_score = min(1.0, 0.5 + (atr_ratio - 1.0) * 0.4) # Scale up to ~0.9
            
        # Priority 2: Ranging (Low Momentum / Compression)
        # ADX < 20 indicates weak trend. BB Width contraction confirms squeeze.
        elif curr_adx < 20 and curr_bb_width < prev_bb_width:
            regime_determined = Regime.RANGING
            confidence_score = min(1.0, 0.6 + (curr_minus_di - curr_plus_di) * 0.1) # Adjust slightly based on lack of expansion

        # Priority 3: Trending Up / Down
        elif curr_adx >= 25: # Strong trend signal
            
            if curr_close > curr_ema_50 and curr_plus_di > curr_minus_di:
                regime_determined = Regime.TRENDING_UP
                confidence_score = min(1.0, 0.6 + (curr_adx / 50)) # Higher ADX = higher confidence
                
            elif curr_close < curr_ema_50 and curr_minus_di > curr_plus_di:
                regime_determined = Regime.TRENDING_DOWN
                confidence_score = min(1.0, 0.6 + (curr_adx / 50))
        
        else:
            # Fallback: Unknown or weak regime
            if curr_close > curr_ema_50:
                regime_determined = Regime.TRENDING_UP
                confidence_score = 0.4
            elif curr_close < curr_ema_50:
                regime_determined = Regime.TRENDING_DOWN
                confidence_score = 0.4
        
        return RegimeState(
            regime=regime_determined,
            confidence=round(confidence_score, 2),
            adx=float(curr_adx),
            atr=float(curr_atr),
            atr_ratio=float(atr_ratio),
            timestamp=datetime.now()
        )

    def _return_unknown_state(self, reason):
        return RegimeState(
            regime=Regime.UNKNOWN,
            confidence=0.0,
            adx=0.0,
            atr=0.0,
            atr_ratio=0.0,
            timestamp=datetime.now()
        )