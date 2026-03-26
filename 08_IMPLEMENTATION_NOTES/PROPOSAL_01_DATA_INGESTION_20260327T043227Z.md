---
DOMAIN: 01_DATA_INGESTION
MODEL: qwen3.5:9b
TIER: cruiser
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

```python
import random
from datetime import datetime, timedelta

def generate_trending(n, start_price, drift_pct, noise_pct):
    """
    Simulates a stock with a clear upward trend based on linear drift + noise.
    """
    candles = []
    current_price = start_price
    
    # Calculate total target increase
    total_increase = (current_price * drift_pct) / 100.0
    step_drift = total_increase / n
    
    # Use a relative start time for reproducibility if seed is configured, 
    # otherwise use datetime now (though this breaks strict reproducibility of timestamps).
    # For reproducibility with random.seed(), we fix the start timestamp here.
    base_time = int(datetime(2023, 1, 1).timestamp() * 1000)
    
    for i in range(n):
        candle_ts = base_time + (i * 60000) # Assuming 1 minute bars or similar
        
        # Drift component
        current_close = current_price + step_drift + (random.random() * 1 - 0.5) * (current_price * noise_pct / 100.0)
        
        candle_open = current_price
        
        # Ensure logical price structure for High/Low
        direction = 'up' if current_close > candle_open else 'down'
        
        if direction == 'up':
            high = max(candle_open, current_close) * (1 + noise_pct / 400.0)
            low = min(candle_open, current_close) * (1 - noise_pct / 200.0)
        else:
            high = max(candle_open, current_close) * (1 + noise_pct / 200.0)
            low = min(candle_open, current_close) * (1 - noise_pct / 400.0)
            
        # Update price for next bar
        current_price = current_close
        
        candles.append({
            "timestamp": candle_ts,
            "open": round(candle_open, 2),
            "high": round(high, 2),
            "low": round(low, 2),
            "close": round(current_close, 2),
            "volume": random.randint(1000, 5000)
        })

    return candles

def generate_mean_reverting(n, center_price, amplitude, noise_pct):
    """
    Simulates a stock mean-reverting to a center price with bounded volatility.
    """
    candles = []
    
    # Initialize starting price randomly near center
    current_price = random.uniform(center_price - amplitude, center_price + amplitude)
    base_time = int(datetime(2023, 1, 1).timestamp() * 1000)
    
    for i in range(n):
        candle_ts = base_time + (i * 60000)
        
        # Pull back to mean with noise
        pull_back_factor = random.uniform(0.8, 1.0) # Oscillates
        drift = (center_price - current_price) * pull_back_factor
        
        change = drift + random.gauss(0, current_price * noise_pct / 200.0) # Gaussian noise
        current_close = current_price + change
        
        candle_open = current_price
        direction = 'up' if current_close > candle_open else 'down'
        
        if direction == 'up':
            high = max(candle_open, current_close) * (1 + random.random() * amplitude / 100.0) # Add swing within amplitude
            low = min(candle_open, current_close) * (1 - random.random() * noise_pct / 500.0)
        else:
            high = max(candle_open, current_close) * (1 + random.random() * amplitude / 100.0)
            low = min(candle_open, current_close) * (1 - random.random() * amplitude / 100.0)
            
        # Constrain price within bounds roughly for sanity
        high = min(high, center_price + amplitude)
        low = max(low, center_price - amplitude)
        
        candles.append({
            "timestamp": candle_ts,
            "open": round(candle_open, 2),
            "high": round(high, 2),
            "low": round(low, 2),
            "close": round(current_close, 2),
            "volume": random.randint(1000, 5000)
        })
        
        current_price = current_close
        
    return candles

def generate_volatile(n, base_price, volatility_pct, noise_pct):
    """
    Simulates a stock with high volatility (large swings).
    """
    candles = []
    current_price = base_price
    base_time = int(datetime(2023, 1, 1).timestamp() * 1000)
    
    for i in range(n):
        candle_ts = base_time + (i * 60000)
        
        # Large random swing
        swing = random.uniform(-volatility_pct/50.0, volatility_pct/50.0) * current_price
        
        candle_open = current_price
        current_close = current_price + swing + random.gauss(0, noise_pct/100.0 * current_price)
        
        direction = 'up' if current_close > candle_open else 'down'
        
        # High/Low spread is determined by volatility
        swing_range = abs(swing) + random.uniform(0, noise_pct/200.0)*current_price
        
        high = max(candle_open, current_close) + swing_range
        low = min(candle_open, current_close) - (random.uniform(0, noise_pct/100.0)*current_price) # Ensure low < open roughly

        candles.append({
            "timestamp": candle_ts,
            "open": round(candle_open, 2),
            "high": round(high, 2),
            "low": round(low, 2),
            "close": round(current_close, 2),
            "volume": random.randint(1000, 5000)
        })
        
        current_price = current_close
        
    return candles

def generate_flash_crash(n, start_price, crash_bar, recovery_bars, noise_pct):
    """
    Simulates a normal walk followed by a sudden crash and subsequent recovery.
    """
    candles = []
    
    # Determine phases
    total_steps = n
    
    for i in range(total_steps):
        candle_ts = int(datetime(2023, 1, 1).timestamp() * 1000) + (i * 60000)
        
        if i < crash_bar:
            # Normal phase
            change = random.uniform(-noise_pct/50.0, noise_pct/50.0) * candles[-1]['close'] if candles else 0
            
        elif i == crash_bar:
            # The crash happens here
            current_price = start_price if not candles else candles[-1]['close']
            # Massive drop
            crash_change = -(random.uniform(0.3, 0.5) * current_price) 
            
        else:
            # Recovery phase (if in recovery bar) or continuing drift
            if i < crash_bar + recovery_bars:
                # Attempt to recover (upward bias)
                change = random.gauss(current_price * noise_pct / 200.0, current_price * 0.01) # Upward bias
            else:
                # Normal noise after recovery period or stabilization
                 change = random.uniform(-noise_pct/200.0, noise_pct/200.0) * current_price

        if i == 0 and candles:
             pass
        
        if not candles:
            current_price = start_price
            
        candle_open = current_price
        candle_close = current_price + change
        
        # Logic to ensure High/Low reflects crash/recovery
        high = max(candle_open, candle_close) * (1.0 + random.random() * noise_pct/500.0)
        low = min(candle_open, candle_close) * (1.0 - random.random() * noise_pct/500.0)
        
        candles.append({
            "timestamp": candle_ts,
            "open": round(candle_open, 2),
            "high": round(high, 2),
            "low": round(low, 2),
            "close": round(candle_close, 2),
            "volume": random.randint(1000, 5000)
        })
        
        current_price = candle_close

    return candles
```