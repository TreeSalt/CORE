---
DOMAIN: 01_DATA_INGESTION
MODEL: qwen3.5:9b
TIER: cruiser
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

Here is the complete Python code to generate synthetic OHLC candlestick data for **Trending**, **Mean-Reverting**, **Volatile**, and **Flash Crash** scenarios as requested.

### Code Explanation
1.  **`generate_trending(n, start_price, drift_pct, noise_pct)`**: Creates an upward trend by adding a consistent positive drift to the price every step, overlaid with Gaussian random noise.
2.  **`generate_mean_reverting(n, center_price, amplitude_pct, noise_pct)`**: Starts at a displaced position and applies a strong pull-back force towards `center_price` in each step. The stronger the deviation from the mean, the stronger the reversion.
3.  **`generate_volatile(n, base_price, noise_pct)`**: Generates high volatility by using a large spread of random noise (uniform distribution) on every step.
4.  **`generate_flash_crash(n, start_price, crash_bar, crash_pct, recovery_bars)`**: Creates a specific spike in volume and price drop at `crash_bar`, followed by a "recovery" phase where the price slowly bounces back up over `recovery_bars` before returning to normal random behavior.

### Python Implementation

```python
from datetime import datetime, timedelta
import random

def generate_trending(n, start_price, drift_pct=1.0, noise_pct=2.0):
    """
    Generates an upward trending candlestick series.
    
    Args:
        n (int): Number of candles to generate.
        start_price (float): Starting price.
        drift_pct (float): Percentage drift upwards per step.
        noise_pct (float): Percentage of random noise added to the drift.
    """
    candles = []
    current_price = start_price
    
    base_time = datetime(2023, 1, 1, 9, 30, 0)
    
    for i in range(n):
        # Calculate price movement: Trend + Noise
        noise_spread = current_price * (noise_pct / 100.0)
        trend_component = current_price * (drift_pct / 100.0)
        
        # Random walk with drift
        close = current_price + trend_component + random.uniform(-noise_spread, noise_spread)
        
        # Construct High/Low around the move
        open_price = current_price
        high = max(open_price, close) + abs(random.uniform(0, noise_spread/3))
        low = min(open_price, close) - abs(random.uniform(0, noise_spread/3))
        
        candles.append({
            'time': base_time + timedelta(minutes=i*5), # Assuming 5 min bars for demo
            'open': round(open_price, 2),
            'high': round(high, 2),
            'low': round(low, 2),
            'close': round(close, 2),
            'volume': int(random.randint(1000, 10000))
        })
        
        current_price = close
        
    return candles

def generate_mean_reverting(n, center_price, amplitude_pct=5.0, noise_pct=3.0):
    """
    Generates a mean-reverting (oscillating) series centered around center_price.
    
    Args:
        n (int): Number of candles.
        center_price (float): The target price the market reverts to.
        amplitude_pct (float): Max deviation from center before pullback.
        noise_pct (float): Noise level.
    """
    candles = []
    current_price = start_price # Logic requires start or first calculated point, usually start near mean
    
    base_time = datetime(2023, 1, 1, 9, 30, 0)
    
    for i in range(n):
        # Calculate distance from center
        distance_from_center = current_price - center_price
        
        # Reversion force: Pull back towards center. 
        # Add a bias opposite to the distance direction.
        reversion_force = -distance_from_center * 0.1 # 0.1 is pullback strength multiplier
        
        noise_spread = current_price * (noise_pct / 100.0)
        
        close = current_price + reversion_force + random.uniform(-noise_spread, noise_spread)
        
        open_price = current_price
        high = max(open_price, close) + abs(random.uniform(0, noise_spread/3))
        low = min(open_price, close) - abs(random.uniform(0, noise_spread/3))
        
        candles.append({
            'time': base_time + timedelta(minutes=i*5),
            'open': round(open_price, 2),
            'high': round(high, 2),
            'low': round(low, 2),
            'close': round(close, 2),
            'volume': int(random.randint(1000, 10000))
        })
        
        current_price = close
        
    return candles

def generate_volatile(n, base_price, noise_pct=50.0):
    """
    Generates a highly volatile series with large OHLC swings.
    
    Args:
        n (int): Number of candles.
        base_price (float): Base price level.
        noise_pct (float): High percentage spread for volatility.
    """
    candles = []
    current_price = base_price
    
    base_time = datetime(2023, 1, 1, 9, 30, 0)
    
    for i in range(n):
        # High noise spread
        noise_spread = current_price * (noise_pct / 100.0)
        
        # Random move with high variance
        close = current_price + random.uniform(-noise_spread, noise_spread)
        
        open_price = current_price
        
        # Ensure high and low are significantly spread due to volatility
        high = max(open_price, close) + abs(random.uniform(0, noise_spread/3))
        low = min(open_price, close) - abs(random.uniform(0, noise_spread/3))
        
        candles.append({
            'time': base_time + timedelta(minutes=i*5),
            'open': round(open_price, 2),
            'high': round(high, 2),
            'low': round(low, 2),
            'close': round(close, 2),
            'volume': int(random.randint(10000, 50000)) # Higher volume for volatility
        })
        
        current_price = close
        
    return candles

def generate_flash_crash(n, start_price, crash_bar, crash_pct=3.0, recovery_bars=10):
    """
    Generates data with a specific flash crash event and subsequent recovery.
    
    Args:
        n (int): Total number of candles.
        start_price (float): Initial price level.
        crash_bar (int): 0-based index where the crash occurs.
        crash_pct (float): Percentage drop during crash relative to open.
        recovery_bars (int): Number of bars after crash to simulate recovery phase.
    """
    candles = []
    current_price = start_price
    
    base_time = datetime(2023, 1, 1, 9, 30, 0)
    
    for i in range(n):
        open_price = current_price
        
        # Determine logic based on bar index
        if i == crash_bar:
            # Flash Crash Logic
            noise_spread = current_price * (5.0 / 100.0)
            drop_pct = crash_pct
            high = open_price + abs(current_price * 0.05) 
            low = current_price - current_price * (crash_pct / 100.0)
            close = low
            volume_spike = int(random.randint(100000, 200000)) # Massive volume
            
        elif i > crash_bar and i < crash_bar + recovery_bars:
            # Recovery Phase Logic (Price attempts to bounce up towards previous levels)
            noise_spread = current_price * (3.0 / 100.0)
            
            # Simple upward bias during recovery to simulate stabilization/repairing price
            recovery_bias = (start_price - current_price) + random.uniform(0, 0.5 * current_price * 0.01)
            close = current_price + recovery_bias + random.uniform(-noise_spread, noise_spread)
            
            high = max(open_price, close) + abs(random.uniform(0, noise_spread/3))
            low = min(open_price, close) - abs(random.uniform(0, noise_spread/3))
            volume_normal = int(random.randint(5000, 10000))

        else:
            # Normal Random Walk logic
            noise_spread = current_price * (2.0 / 100.0)
            close = current_price + random.uniform(-noise_spread, noise_spread)
            
            high = max(open_price, close) + abs(random.uniform(0, noise_spread/3))
            low = min(open_price, close) - abs(random.uniform(0, noise_spread/3))
            volume_normal = int(random.randint(1000, 10000))

        candles.append({
            'time': base_time + timedelta(minutes=i*5),
            'open': round(open_price, 2),
            'high': round(high, 2),
            'low': round(low, 2),
            'close': round(close, 2),
            'volume': volume_spike if i == crash_bar else volume_normal
        })
        
        current_price = close
        
    return candles

# Example Usage
if __name__ == "__main__":
    # Generate a trending series of length 100 starting at 50
    trend_data = generate_trending(100, start_price=50.0)
    
    # Generate a mean reversion series centered at 100
    reverting_data = generate_mean_reverting(n=100, center_price=100.0)
    
    # Generate highly volatile data
    vol_data = generate_volatile(100, base_price=60.0)
    
    # Generate flash crash at index 30 with a drop of 3%
    crash_data = generate_flash_crash(n=100, start_price=50.0, crash_bar=30, crash_pct=3.0)
    
    print(f"Generated {len(trend_data)} trending candles.")
    print(f"First Trend Candle: {trend_data[0]}")
    print(f"Crash Event at index 30: {crash_data[30]}")

```