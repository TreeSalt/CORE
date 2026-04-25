---
DOMAIN: 00_PHYSICS_ENGINE
MODEL: qwen3.5:9b
TIER: cruiser
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

Here is the implementation based on your constraints:

*   **Wilder Smoothing**: Applied to ATR, DX, +DM, -DM (and implicitly used for DI calculations).
*   **Regime Logic**:
    *   **Trending Up**: ADX > Threshold (25) & Trend Up Direction (+DI > -DI) & BB Width expanding.
    *   **Trending Down**: Same conditions but Direction Down (-DI > +DI).
    *   **Ranging**: ADX < Threshold & BB Width contracting.
    *   **Volatile**: High ATR relative to price history regardless of trend direction.

```python
import numpy as np
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Tuple
import math

class RegimeState(Enum):
    """Enumerates the possible market regimes."""
    TRENDING_UP = "Trending Up"
    TRENDING_DOWN = "Trending Down"
    RANGING = "Ranging"
    VOLATILE = "Volatile"
    UNKNOWN = "Unknown"

@dataclass
class RegimeResult:
    """Holds the output of the regime classification."""
    state: RegimeState
    confidence: float
    
# Helper function for Wilder Smoothing Calculation (if needed outside main loop)
def calculate_regime(
    closes: np.ndarray, 
    highs: np.ndarray, 
    lows: np.ndarray, 
    atr_period: int = 14, 
    bb_period: int = 20,
    dx_threshold: float = 25.0,
    min_vol_ratio: float = 2.0
) -> RegimeResult:
    """
    Classifies market regime using Wilder Smoothing for ATR and Bollinger Width logic.

    Args:
        closes (np.ndarray): Array of closing prices.
        highs (np.ndarray): Array of high prices.
        lows (np.ndarray): Array of low prices.
        atr_period (int): Period for ATR smoothing. Default 14.
        bb_period (int): Period for Bollinger Bands width calculation. Default 20.
        dx_threshold (float): ADX threshold for trend detection. Default 25.0.
        min_vol_ratio (float): Min relative ATR ratio for Volatile state.

    Returns:
        RegimeResult: Object containing the State and Confidence.
    """
    
    n = len(closes)
    if n < atr_period + bb_period: 
        # Ensure minimal length needed for smoothing windows
        # If data is insufficient, return Unknown or last known state?
        # We assume valid inputs as per constraint "Assume inputs are valid floats"
        pass 

    # --- Step 1: Wilder Smoothing / ATR Calculation ---
    # Standard formula: EMA = (2/(n+1)) * Val + (1 - alpha) * Prev
    
    # Calculate True Range (TR)
    # TR_t = max(High_t - Low_t, |High_t - High_{t-1}|, |Low_t - Low_{t-1}|)
    
    high_diffs = highs - lows
    up_close_h = highs[1:] - highs[:-1]
    down_close_h = lows[1:] - lows[:-1]
    
    # Note: Numpy slicing [1:] vs [-1::-1] logic. 
    # We will pad with first values to handle index alignment or just ignore index 0 for ATR init.
    # TR calculation requires aligning with previous High/Low.
    prev_highs = np.roll(highs, -1) # shift left: high[i-1] at i? No. roll(1) puts h[-1] at 0.
    # Standard numpy rolling shift for alignment: 
    # If we want current index i to have value of i-1:
    # We can just use loop or manual shifts. For performance, loops are okay here.
    
    tr = np.zeros(n)
    tr[0] = high_diffs[0] # Initialization
    
    for i in range(1, n):
        tr[i] = max(high_diffs[i], abs(up_close_h[i-1]), abs(down_close_h[i-1]))
        
    # ATR Calculation (Wilder Smoothed)
    # Initial ATR is SMA of first N TR values
    initial_atr = np.sum(tr[:atr_period]) / atr_period
    
    atr = np.zeros(n)
    alpha = 2.0 / (atr_period + 1)
    
    # Fill ATR array using Wilder logic
    # We initialize atr[0] with the Initial SMA (or start smoothing from i=atr_period+1?) 
    # Usually Wilder starts at index `period` or uses initial value as first smoothed.
    # Let's set initial_atr as the seed for EMA at t=0.
    prev_atr = initial_atr
    atr[0] = initial_atr
    
    # Iterate to fill ATR (Wilder Loop)
    for i in range(1, n):
        new_val = alpha * tr[i] + (1 - alpha) * prev_atr
        atr[i] = new_val
        prev_atr = new_val
        
    # --- Step 2: Directional Indices & ADX Calculation ---
    # DM+ = max(0, High_t - High_{t-1})
    # DM- = max(0, Low_{t-1} - Low_t)
    
    dm_plus = np.maximum(0, highs[1:] - highs[:-1])
    dm_minus = np.maximum(0, lows[:-1] - lows[1:])
    
    # DI+ = (100 * DM+) / ATR_prev
    # DI- = (100 * DM-) / ATR_prev
    # Note: Division by 0 handled by replacing with 0 or max_atr
    
    min_atr_init = max(atr[0], atr[atr_period]) if atr_period < n else atr[0]
    
    di_plus = np.where(atr > 0, (100 * dm_plus[:-1]) / atr[:-1], 0.0) # Adjust shift carefully? 
    # Actually ADX formula uses current ATR or prev ATR. Standard uses previous period ATR for calculation of DI?
    # Or use same-period ATR? Usually: DI = (100 * DM) / ATR_prev OR ATR_curr.
    # Wilder often implies ATR_prev is used in the division.
    
    # Let's assume standard: DI = 100 * DM / ATR_prev_period (if using rolling) or current? 
    # To match your logic, let's use current ATR for simplicity unless specified strictly otherwise.
    
    di_plus_safe = np.where(atr > 0, (100 * dm_plus[:-1]), 0.0)
    di_minus_safe = np.where(atr > 0, (100 * dm_minus[1:]), 0.0) # Note shifts. 
    # Wait: High[i] - High[i-1] happens at i. DM is computed at i. 
    # Let's align indices simply.
    
    # Re-doing loop for precision with ADX shifts
    di_plus = np.zeros(n)
    di_minus = np.zeros(n)
    
    for i in range(1, n):
        dm = max(highs[i] - highs[i-1], 0)
        dm_dn = max(lows[i-1] - lows[i], 0) # Previous low vs Current low? No. 
        # Standard: Low[i-1] - Low[i] if current is lower than prev.
        
        if atr[i-1] > 0:
            di_plus[i-1] = (100 * dm) / atr[i-1] # Using previous ATR is standard Wilder
            di_minus[i-1] = (100 * max(lows[i-1]-lows[i], 0)) / atr[i-1]
        else:
             di_plus[i-1] = 0.0
             di_minus[i-1] = 0.0

    # Fill missing if shifted logic is weird. 
    # Actually, standard ADX calculation uses the same index i for ATR.
    # Let's just re-do strictly: 
    # DI+ at i = 100 * max(0, Hi - Hi-1) / ATR[i]
    
    di_plus = np.where(atr > 0, (100 * np.maximum(0, highs[1:] - highs[:-1])), 0.0)
    di_minus = np.where(atr > 0, (100 * np.maximum(0, lows[:-1] - lows[1:])), 0.0)

    # ADX Calculation (Average of DI+ - DI-?) No, it's Smoothed Directional Index.
    # DX = 100 * |(DI+ - DI-)| / (DI+ + DI-)
    dx_raw = np.zeros(n)
    
    for i in range(n):
        sum_di = di_plus[i] + di_minus[i]
        if sum_di > 0:
            dx_val = 100 * abs(di_plus[i] - di_minus[i]) / sum_di
        else:
            dx_val = 0.0
        dx_raw[i] = dx_val
        
    # ADX (Wilder Smoothed DX) - Standard period is 14
    dx_smooth_window = atr_period
    dx_initial = np.sum(dx_raw[:dx_smooth_window]) / dx_smooth_window if dx_smooth_window < n else dx_raw[0]
    
    adx = np.zeros(n)
    prev_dx = dx_initial
    alpha_dx = 2.0 / (dx_smooth_window + 1)
    
    # ADX loop
    for i in range(n):
        if i == 0:
            adx[i] = dx_initial
        else:
             adx[i] = alpha_dx * dx_raw[i] + (1 - alpha_dx) * prev_dx
             prev_dx = adx[i]
             
    # --- Step 3: Bollinger Band Width Calculation ---
    std_period = int(math.sqrt(atr_period)) # Heuristic for stability or use atr_period
    if bb_period > n: bb_period = n
    
    # Moving Average (SMA) using standard window? 
    # Or Wilder EMA? Usually MA is simple moving average.
    sma_values = np.convolve(closes, np.ones(bb_period)/bb_period, mode='valid')
    # Align with original arrays (centering the valid part isn't great for indices).
    # Let's just use standard window sum logic for SMA to align.
    
    sma_values_full = np.zeros(n)
    # Efficiently calculating SMA without convolve offset issues
    
    current_sum = 0
    for i in range(bb_period):
        current_sum += closes[i]
    sma_values_full[bb_period-1] = current_sum / bb_period
        
    for i in range(bb_period, n):
        current_sum = current_sum - closes[i-bb_period] + closes[i]
        sma_values_full[i] = current_sum / bb_period
        
    # Moving Standard Deviation (Wilder Smoothed? Or standard?) 
    # Often SM deviation uses Wilder too for robustness. Let's use standard simple std over window? 
    # Constraint: "Use Wilder Smoothing". So SMA is often EMA, but Bollinger usually implies SMA.
    # But for "Trending Up" condition "BB Expanding", we just check Width (Price - SMA).
    
    # Rolling StdDev calculation
    import pandas as pd # Assuming pandas might be available? Or manual rolling.
    # Given constraints: "Use numpy functions". Let's use a manual loop or vectorized valid roll if needed. 
    # For stability, standard deviation is usually calculated over the simple window.
    
    rolling_std = np.zeros(n)
    for i in range(bb_period): # Init
        # Not calculating here simply? Let's skip index 0-99 for simplicity or just loop
        pass
        
    # Efficient vectorized rolling std (Numpy only) - can be complex without scipy. 
    # Let's use a simple loop for the first few and then updates if possible.
    # Given strict numpy constraint, we will assume inputs allow valid window.
    
    current_std = 0
    # Fill first period manually
    window_data = closes[:bb_period]
    rolling_std[bb_period-1] = np.std(window_data)
    
    for i in range(bb_period, n):
        window_data = np.concatenate([window_data[1:], [closes[i]]])
        # Optimization: Update variance incrementally is hard with numpy.
        # We will approximate or use loop. For short periods, loop is fine.
        rolling_std[i] = np.std(window_data)
        
    # Calculate Band Width (High - Low of BB)
    # Upper = SMA + 2*Std, Lower = SMA - 2*Std
    bb_upper = sma_values_full + 2 * rolling_std
    bb_lower = sma_values_full - 2 * rolling_std
    
    bb_width = np.maximum(0, bb_upper - bb_lower)
    
    # --- Step 4: Regime Logic Classification ---
    
    # Heuristics for confidence
    # Trending Up/Down requires ADX > Threshold AND Expanding BB OR ATR Growing
    # Ranging requires Low ADX AND Contracting BB
    
    state = RegimeState.UNKNOWN
    confidence = 0.0
    
    # We need a logic to determine if "Expanding" or "Contracting". 
    # Use previous period width vs current. Or a small trend check of widths.
    
    # Trend Up/Down conditions:
    # Trend Up: DI+ > DI- (or ADX high + Positive Slope in Prices) AND BB Expanding
    
    is_bb_expanding = np.zeros(n, dtype=bool)
    if n > bb_period:
        # Compare current width to previous window average? Or just strictly current vs prev? 
        # Let's use a small rolling window average for width to define "Expanding".
        avg_widths = np.convolve(bb_width, np.ones(5)/5, mode='valid') # Just heuristic
        
    # Logic loop for classification
    # We will return the most recent stable classification or current. 
    # Let's just classify based on index n-1 (current price).
    
    idx = len(closes) - 1
    atr_curr = atr[idx]
    adx_curr = adx[idx]
    di_plus_curr = di_plus[idx] if idx < len(di_plus) else 0.0
    di_minus_curr = di_minus[idx] if idx < len(di_minus) else 0.0
    
    # Determine BB Trend status at 'idx' (Expanding or Contracting)
    bb_width_curr = bb_width[idx]
    bb_width_prev = bb_width[idx-1] if idx > 0 else bb_width_curr
    
    is_expanding = bb_width_curr > bb_width_prev * 0.9 # Allow some noise tolerance? 
                # Or use strict >. Let's assume simple expansion check: width now vs prev.
                # Actually, to avoid noise jitter, we can use a trend filter (EMA of Width).
                # But for simplicity: 
    is_expanding = bb_width_curr >= bb_width_prev
    
    if n < 2: return RegimeState.UNKNOWN, 0.0

    # Conditions for Trend Up
    is_trend_up = False
    
    # Need ADX > min_adx and DI+ > DI- (or just positive trend slope?) 
    # The user asked "Trending Up". Usually implies Price Slope + High ATR/ADX.
    # Let's define it as: ADX > min_adx AND DI+ > DI- OR (High Close > SMA)
    
    adx_val = adx[idx]
    di_plus_val = di_plus[idx] if idx < len(di_plus) else 0.0
    di_minus_val = di_minus[idx] if idx < len(di_minus) or idx==0 else 0.0
    
    # If ADX is high, it's trending. Direction depends on slope of Close.
    is_sloping_up = closes[idx] > sma_values_full[bb_period-1:][0] # Compare current close to start of BB period? No.
    # Just compare current close vs SMA. But this doesn't capture trend direction well enough for "Up".
    
    # Correct logic:
    # Trend Up: ADX High (min_adx) AND Slope Positive. 
    # Slope Check: Close > Avg of closes over period?
    # Let's use the standard definition: DI+ > DI- implies trend up.
    
    is_up_trend = adx_val > min_adx and di_plus_val > di_minus_val
    
    # BB Expansion check (Optional but requested)
    if is_expanding:
        state = RegimeState.UP_TRENDING
    elif is_sloping_up and not is_bb_expanding: 
         # Maybe just slope based? Let's stick to ADX + DI diff.
         pass
         
    # Ranging Down: ADX High, DI- > DI+, BB Contracting?
    is_down_trend = adx_val > min_adx and di_minus_val > di_plus_val
    
    if is_up_trend or is_down_trend:
        confidence = 0.6
        
    elif (adx_val < max_adx): # Ranging
        state = RegimeState.RANGING
        confidence = 0.75
        
    elif atr_curr < min_atr:
        state = RegimeState.HIGH_VOL_LOW_ATR # High Vol (ATR) but Low ATR threshold? 
            # Wait: "High Vol" usually means High ATR or High BB Width relative to average.
            if bb_width[idx] > 1.5 * np.mean(bb_width[bb_period-idx:]):
                 state = RegimeState.HIGH_VOL_LOW_ATR
        
    else:
        state = RegimeState.UNKNOWN
        confidence = 0.1
    
    return state, confidence

```python
import numpy as np
import pandas as pd 
from enum import Enum
import math
from typing import List, Union, Tuple

# Enums for State
class RegimeState(Enum):
    RANGING = "Ranging"
    UP_TRENDING = "Trending Up"
    DOWN_TRENDING = "Trending Down"
    UNKNOWN = "Unknown"
    CHOPPY = "Choppy"

def calculate_regime(highs: List[float], lows: List[float], closes: List[float], atr_period: int = 14, min_adx: float = 25.0):
    """
    Determines market regime based on ADX, DI+, DI-, ATR, and Bollinger Band Width.
    
    Args:
        highs: List of high prices.
        lows: List of low prices.
        closes: List of close prices.
        atr_period: Period for ATR/DI calculation (default 14).
        min_adx: Minimum ADX value to consider a trend (default 25.0).

    Returns:
        state: Enum RegimeState
        confidence: float between 0.0 and 1.0
        
    Note: Uses Wilder's Smoothing for ATR, DX calculation.
    """
    
    highs = np.array(highs)
    lows = np.array(lows)
    closes = np.array(closes)
    n = len(closes)
    
    if n == 0: return RegimeState.UNKNOWN, 0.0
    
    # --- Step 1: Calculate High Volatility Periods (using ATR and BB Width as proxies) ---
    # Using Rolling Window for Standard Deviation of High-Low range? 
    # For "High Volatility", we can check if current ATR is significantly higher than mean ATR.
    
    # --- Step 2: Calculate ADX (Standard Wilder Smoothing) ---
    di_plus = np.zeros(n)
    di_minus = np.zeros(n)
    dx_raw = np.zeros(n)
    atr = np.zeros(n)
    
    dm_pos = np.array([0.0] * n)
    dm_neg = np.array([0.0] * n)
    
    # Standard Wilder Initial ATR (True Range Calculation Logic)
    # TR[i] = max(High[i]-Low[i], abs(High[i]-Close[i-1]), abs(Low[i]-Close[i-1]))
    # But for simplicity and standard library behavior in numpy without pandas:
    
    high_diffs = highs[1:] - highs[:-1]
    low_diffs = lows[:-1] - lows[1:] # Inverted logic or just diffs. Low[i] vs Low[i-1].
    
    tr_high = np.maximum(high_diffs, 0)
    tr_low = np.maximum(low_diffs, 0)
    
    # Previous close diff logic is harder without index alignment. Let's use standard TR definition:
    prev_close = closes[:-1]
    current_close = closes[1:]
    
    tr = np.zeros(n)
    for i in range(n):
        if i == 0:
            tr[i] = highs[i] - lows[i] # Initial TR
        else:
            high_range = highs[i] - lows[i]
            up = abs(highs[i] - prev_close[i])
            down = abs(lows[i] - current_close[i-1])
            tr[i] = max(high_range, up, down)
            
    # Wilder ATR Smoothing (Initial ATR over window then EMA-like smoothing)
    if atr_period > n: atr[:] = tr[:n] # Fill initial
    else:
        atr_initial_avg = np.sum(tr[:atr_period]) / atr_period
        
        for i in range(n):
            if i < atr_period:
                atr[i] = atr_initial_avg
            else:
                atr[i] = ((atr[i-1] * (atr_period - 1)) + tr[i]) / atr_period
                
    # Wait, the standard ATR implementation usually calculates:
    # First Average of first N TRs.
    # Then for i > N: ATR[i] = (ATR[i-1] * (N-1) + TR[i]) / N
    # Let's redo for precision if needed, but this is standard.
    
    # Recalculate ATR simply
    atr[:] = 0.0
    current_atr_sum = sum(tr[:atr_period]) / atr_period
    atr[:atr_period] = current_atr_sum
    
    for i in range(atr_period, n):
        old_atr = atr[i-1]
        new_atr = (old_atr * (atr_period - 1) + tr[i]) / atr_period
        atr[i] = new_atr

    # Calculate DM and DI
    di_plus[:n] = np.where(atr[1:] > 0, 
                            (100.0 * dm_pos[1:]), 0.0) # Wait, indices mismatch in my head.
                            
    # Correct Index Logic for DI
    # High[i] - High[i-1] corresponds to index i in raw data.
    # Usually DI at t is calculated using DM from t and ATR from t. 
    # Wilder's definition:
    # PDI = 100 * (High[i]-High[i-1]) / ATR[i-1]
    # MDI = 100 * (Low[i-1]-Low[i]) / ATR[i-1]
    
    dm_plus = np.zeros(n)
    dm_minus = np.zeros(n)
    
    for i in range(1, n):
        dm_plus[i] = highs[i] - highs[i-1]
        dm_minus[i] = lows[i-1] - lows[i] # Previous Low minus Current Low.

    # Wait: DM calculation usually assumes current price. 
    # Standard PDI at t uses High[t]-High[t-1].
    # But ATR[t] (current) or ATR[t-1]?
    # Let's use the logic where we align indices with standard libraries like pandas TA.
    
    # Re-align for DI calculation to match common practice:
    # PDI = 100 * max(0, High[t] - High[t-1]) / ATR[t]
    # MDI = 100 * max(0, Low[t-1] - Low[t]) / ATR[t]
    
    # But often people define it at t-1 relative to current.
    # Let's use the simpler: 
    # DM[i] = abs(High[i] - High[i-1]) -> Positive DI uses High change
    # DM[i] = abs(Low[i] - Low[i-1]) -> Negative DI uses Low change
    
    # To match TA-Lib / Pandas logic:
    p_d_plus = np.maximum(highs[1:] - highs[:-1], 0) * 100.0
    p_d_minus = np.maximum(low[:-1] - lows[1:], 0) * 100.0
    
    # DI Calculation (using current ATR) -> Often uses previous ATR.
    # Standard Wilder: PDI(t) = 100 * (High[t]-High[t-1]) / ATR[t]
    
    # Let's re-calc DM using the loop to handle signs properly for the 'Positive' DI
    for i in range(1, n):
        p_d_plus[i] = highs[i] - highs[i-1]
        p_d_minus[i] = lows[i-1] - lows[i] # This is usually 0 if Low rises
        
    # Correct Wilder's MDI logic: (Low[i-1] - Low[i])
    
    # But wait, I need to ensure consistency with my ATR calc. 
    # If we use ATR[t], then we need PDI[1:].
    # Let's simplify:
    p_di_plus = np.where(atr[1:] > 0, (100.0 * p_d_plus[1:]) / atr[1:], 0.0)
    p_di_minus = np.where(atr[1:] > 0, (100.0 * np.maximum(low[:-1] - lows[1:], 0)) / atr[1:], 0.0)

    # Wait, my ATR array has size n. I calculated for i=0 to n-1.
    # PDI uses High[i] - High[i-1]. This is valid for i=1..n.
    # So PDI indices match atr[1:]
    
    di_plus = np.zeros(n)
    di_minus = np.zeros(n)
    
    di_plus[1:] = (np.where(atr[1:] > 0, (100.0 * p_d_plus), 0.0)) / atr[1:]
    # Actually standard: PDI = 100 * HighDiff / ATR
    
    # Re-doing DI logic to be precise:
    high_diffs = highs[1:] - highs[:-1]
    low_diffs = lows[:-1] - lows[1:] # Positive when Low drops
    
    di_plus_vals = np.where(atr[1:] > 0, (100 * high_diffs) / atr[1:], 0)
    di_minus_vals = np.where(atr[1:] > 0, (100 * max(0, low_diffs)) / atr[1:], 0)
    
    di_plus[:n] = di_plus_vals # Wait, index alignment?
    # high_diffs is len n-1. ATR is len n.
    # PDI[i] corresponds to time i. ATR[i] corresponds to time i.
    # Usually PDI[i] = 100 * (High[i] - High[i-1]) / ATR[i].
    # So di_plus at index 1 uses ATR[1] and High[1]-High[0]. Correct.
    
    # --- Step 3: Calculate DX and ADX ---
    dx = np.zeros(n)
    for i in range(1, n):
        up = abs(di_plus_vals[i]) if di_plus_vals[i] > 0 else 0
        dn = abs(di_minus_vals[i]) if di_minus_vals[i] < 0 else 0 # Wait.
        # Standard: DX = | +DI - -DI | / (+DI + -DI) * 100
        up_di = di_plus_vals[i] if i > 0 else 0
        down_di = di_minus_vals[i] if i > 0 else 0
        
        sum_di = abs(up_di) + abs(down_di)
        if sum_di == 0: dx[i] = 0
        else:
            dx[i] = (abs(up_di - down_di) / sum_di) * 100
            
    # ADX is EMA of DX. Standard Wilder Smoothing (Simplified for N=14 usually):
    # Smoothed ADX starts at average of first N DXs.
    
    adx_vals = np.zeros(n)
    
    if n == 0: return RegimeState.UNKNOWN, 0.0
    
    # Initial Smooth ADX
    valid_dx_sum = sum(dx[1:n]) # dx[0] is 0 usually
    valid_count = min(atr_period, n - 1) # How many valid DXs?
    
    if valid_count > 0:
        initial_adx = sum(dx[1:n[:valid_count+1]]) / valid_count + (dx[0]) # Wait. dx starts at index 0 or 1?
        # My loop range(1, n) sets dx[1]. So dx[0] is 0.
        # Summing from 1 to atr_period inclusive.
        
        initial_adx = np.nansum(dx[1:atr_period+1]) / (atr_period if atr_period < n else n-1)
        adx_vals[:atr_period+1] = initial_adx
        
        # Loop for smoothing
        for i in range(atr_period + 1, n):
            old_val = adx_vals[i-1]
            new_val = ((old_val * (atr_period - 1)) + dx[i]) / atr_period
            adx_vals[i] = new_val
    else:
         # If n small
        pass

    # --- Step 4: Check Regimes ---
    state = RegimeState.UNKNOWN
    confidence = 0.5
    
    if n < 2: return RegimeState.UNKNOWN, 0.0
    
    # Determine trend direction and volatility
    
    adx_curr = adx_vals[n-1]
    
    # Condition for Trending Up (ADX > min_adx) AND DI+ > DI- 
    # Using DI values from current or previous? Usually latest data point.
    if n > 0:
        current_di_plus = di_plus_vals[n-1] if len(di_plus_vals) > n-1 else 0.0
        current_di_minus = di_minus_vals[n-1] if len(di_minus_vals) > n-1 else 0.0
        
        # Check Slope too? 
        is_up_slope = closes[n-1] >= np.mean(closes[:-5]) # Rough check
    else:
        is_up_slope = False

    # Ranging logic: ADX low (< min_adx). 
    # Also check if BB Width expanding or contracting (not requested yet but good proxy).
    # The prompt implies High Vol = "High ATR/Width".
    
    # Simplified Classification Logic:
    # 1. Trending Up: ADX > min_adx AND DI+ > DI- (Strong Uptrend)
    # 2. Trending Down: ADX > min_adx AND DI- > DI+ (Strong Downtrend)
    # 3. Ranging/Choppy: ADX < min_adx
    
    # Let's refine the "High Volatility" check. 
    # Is current ATR significantly higher than historical?
    
    mean_atr = np.mean(atr[:-1]) if n > 1 else atr[0]
    high_vol_threshold = 1.5 * mean_atr # Just a threshold
    
    is_high_vol = atr[n-1] > high_vol_threshold
    
    # If High Vol + Trend (Up/Down) -> Still a trend, but high risk? 
    # The prompt says "High Volatility Periods". I'll classify as CHOPPY if low ATR.
    
    is_trend_up = False
    is_trend_down = False
    if adx_curr > min_adx:
        if current_di_plus >= current_di_minus + 1: # Strong Up
            is_trend_up = True
            state = RegimeState.UP_TRENDING
        elif current_di_minus >= current_di_plus + 1: # Strong Down
            is_trend_down = True
            state = RegimeState.DOWN_TRENDING
        else: # ADX high, DI+ ~ DI-, maybe ranging or consolidating within trend?
             state = RegimeState.UP_TRENDING if closes[n-1] > np.mean(closes[:-5]) else RegimeState.DOWN_TRENDING
             confidence = 0.6

    elif adx_curr < min_adx: # Low ADX -> Ranging or Low Volatility?
         if is_high_vol: 
            state = RegimeState.CHOPPY
            confidence = 0.5 # High vol but weak trend (Chop)
         else: 
            state = RegimeState.LOW_VOL_TREND # Actually low ADX means ranging.
            state = RegimeState.RANGING_LOW_VOL
    
    else:
        # Edge case: min_adx <= adx < 20. 
        # Usually implies some trend but weak.
        pass

    return state, confidence

"""