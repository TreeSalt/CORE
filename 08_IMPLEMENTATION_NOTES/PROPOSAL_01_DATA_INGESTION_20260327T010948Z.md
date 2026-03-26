---
DOMAIN: 01_DATA_INGESTION
MODEL: qwen3.5:9b
TIER: cruiser
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

import random
from datetime import datetime, timedelta

def generate_trending(n, start_price, drift_pct, noise_pct, seed=None):
    """
    Generates a synthetic candlestick dataset with a linear trend and Gaussian noise.
    
    Args:
        n (int): Number of candles to generate.
        start_price (float): Initial price for the first candle.
        drift_pct (float): Percentage drift per candle (e.g., 2 for 0.02% total over n candles).
        noise_pct (float): Volatility magnitude percentage (std dev relative to price).
        seed (int, optional): Random seed for reproducibility.
    
    Returns:
        List of dicts with keys: timestamp, open, close, high, low, volume.
    """
    if seed is not None:
        random.seed(seed)

    candles = []
    base_time = datetime(2024, 1, 1, 0, 0, 0)
    current_price = start_price
    
    # Calculate total linear trend value distributed over n steps
    # Note: drift_pct is treated as the total percentage shift to achieve over the period
    total_drift_val = start_price * (drift_pct / 100.0)
    trend_step = total_drift_val / n

    for i in range(n):
        interval_time = base_time + timedelta(minutes=i+1)
        
        noise_val = random.gauss(0, current_price * (noise_pct / 100.0))
        
        # Apply linear trend step
        close = current_price + trend_step + noise_val
        
        open_p = current_price
        
        high = max(open_p, close) + random.uniform(0, current_price * 0.005)
        low = min(open_p, close) - random.uniform(0, current_price * 0.005)
        
        candles.append({
            'timestamp': interval_time,
            'open': round(float(open_p), 2),
            'close': round(float(close), 2),
            'high': round(float(high), 2),
            'low': round(float(low), 2),
            'volume': random.randint(100, 1000)
        })
        
        current_price = close
    
    return candles

def generate_mean_reverting(n, center_price, amplitude_pct, noise_pct, seed=None):
    """
    Generates a synthetic candlestick dataset mean-reverting towards a central price.
    
    Args:
        n (int): Number of candles to generate.
        center_price (float): The equilibrium price target.
        amplitude_pct (float): Maximum deviation intensity (pull strength).
        noise_pct (float): Volatility magnitude percentage.
        seed (int, optional): Random seed for reproducibility.
    
    Returns:
        List of dicts with keys: timestamp, open, close, high, low, volume.
    """
    if seed is not None:
        random.seed(seed)

    candles = []
    base_time = datetime(2024, 1, 1, 0, 0, 0)
    current_price = center_price
    
    for i in range(n):
        interval_time = base_time + timedelta(minutes=i+1)
        
        noise_val = random.gauss(0, current_price * (noise_pct / 100.0))
        
        deviation = current_price - center_price
        
        # Pull force towards center: negative correlation with deviation
        pull_force = deviation * (-amplitude_pct / 200.0)
        
        close = current_price + noise_val + pull_force
        
        open_p = current_price
        
        high = max(open_p, close) + random.uniform(0, current_price * 0.005)
        low = min(open_p, close) - random.uniform(0, current_price * 0.005)
        
        candles.append({
            'timestamp': interval_time,
            'open': round(float(open_p), 2),
            'close': round(float(close), 2),
            'high': round(float(high), 2),
            'low': round(float(low), 2),
            'volume': random.randint(100, 1000)
        })
        
        current_price = close
    
    return candles

def generate_volatile(n, start_price, volatility_pct, seed=None):
    """
    Generates a synthetic candlestick dataset with high random volatility.
    
    Args:
        n (int): Number of candles to generate.
        start_price (float): Initial price for the first candle.
        volatility_pct (float): Magnitude of price movement percentage per step.
        seed (int, optional): Random seed for reproducibility.
    
    Returns:
        List of dicts with keys: timestamp, open, close, high, low, volume.
    """
    if seed is not None:
        random.seed(seed)

    candles = []
    base_time = datetime(2024, 1, 1, 0, 0, 0)
    current_price = start_price
    
    for i in range(n):
        interval_time = base_time + timedelta(minutes=i+1)
        
        noise_val = random.gauss(0, current_price * (volatility_pct / 50.0)) # Amplified volatility
        
        change = noise_val
        
        close = current_price + change
        
        open_p = current_price
        
        high = max(open_p, close) + abs(change) * 0.5
        low = min(open_p, close) - abs(change) * 0.5
        
        candles.append({
            'timestamp': interval_time,
            'open': round(float(open_p), 2),
            'close': round(float(close), 2),
            'high': round(float(high), 2),
            'low': round(float(low), 2),
            'volume': random.randint(100, 1000)
        })
        
        current_price = close
    
    return candles

def generate_flash_crash(n, start_price, crash_bar_index, crash_pct, recovery_rate, noise_pct, seed=None):
    """
    Generates a dataset with an instantaneous price drop (crash) at a specific bar index.
    
    Args:
        n (int): Number of candles to generate.
        start_price (float): Initial price for the first candle.
        crash_bar_index (int): Index where crash occurs (0-based).
        crash_pct (float): Percentage drop during crash.
        recovery_rate (float): Multiplier for recovery speed.
        noise_pct (float): Normal market noise magnitude percentage.
        seed (int, optional): Random seed for reproducibility.
    
    Returns:
        List of dicts with keys: timestamp, open, close, high, low, volume.
    """
    if seed is not None:
        random.seed(seed)

    candles = []
    base_time = datetime(2024, 1, 1, 0, 0, 0)
    current_price = start_price
    
    for i in range(n):
        interval_time = base_time + timedelta(minutes=i+1)
        
        if i < crash_bar_index:
            # Normal noisy walk
            noise_val = random.gauss(0, current_price * (noise_pct / 50.0))
            close = current_price + noise_val
        elif i == crash_bar_index:
            # Apply crash at this bar
            crash_drop = current_price * (crash_pct / 100.0)
            close = current_price - crash_drop
            
            # Open for crash is same as prev close
            open_p = current_price
            high = max(open_p, close) + random.uniform(0, current_price * 0.005)
            low = min(open_p, close) - crash_drop * recovery_rate * 0.1
            
        else:
            # Recovery phase
            noise_val = random.gauss(0, current_price * (noise_pct / 50.0))
            recovery_add = (start_price - current_price) * recovery_rate * 0.5 + noise_val
            
            close = current_price + recovery_add
        
        open_p = current_price
        
        high = max(open_p, close) + random.uniform(0, current_price * 0.005)
        low = min(open_p, close) - random.uniform(0, current_price * 0.005)
        
        candles.append({
            'timestamp': interval_time,
            'open': round(float(open_p), 2),
            'close': round(float(close), 2),
            'high': round(float(high), 2),
            'low': round(float(low), 2),
            'volume': random.randint(100, 1000)
        })
        
        current_price = close
    
    return candles<|endoftext|><|im_start|>user