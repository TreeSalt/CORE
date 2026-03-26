---
DOMAIN: 01_DATA_INGESTION
MODEL: qwen3.5:9b
TIER: cruiser
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

Here are the three Python functions designed to generate synthetic candlestick data for a financial dataset. Each function simulates a different market behavior as requested: trend following, mean reversion, and a flash crash with recovery.

### 1. `generate_trending`
Generates data that shows a consistent upward movement (bullish trend).

```python
import random

def generate_trending(n, start_price, growth_rate):
    """
    Generates n candlesticks with a positive trend.
    
    Args:
        n (int): Number of candles to generate.
        start_price (float): Starting price of the first candle.
        growth_rate (float): Expected growth rate per step (e.g., 0.01 for 1% drift).
        
    Returns:
        List of dicts containing 'open', 'high', 'low', 'close'.
    """
    candles = []
    current_price = start_price
    
    for _ in range(n):
        # Add noise around current price
        noise = random.uniform(-current_price * 0.01, current_price * 0.01)
        open_p = current_price + noise
        
        # Simulate volatility (High/Low spread)
        high_noise = abs(random.uniform(current_price * 0.005, current_price * 0.02))
        low_noise = abs(random.uniform(current_price * 0.005, current_price * 0.02))
        
        # Base High/Low around Open/Close logic
        high_p = max(open_p, current_price) + high_noise
        low_p = min(open_p, current_price) - low_noise
        
        # Apply trend: Close moves up relative to Open
        close_p = open_p + random.gauss(0, current_price * growth_rate)
        
        # Ensure OHLC validity (Standard Candle Logic)
        if open_p > close_p:
            high_p = max(high_p, open_p)
            low_p = min(low_p, close_p)
        else:
            high_p = max(high_p, close_p)
            low_p = min(low_p, open_p)
            
        # Update price for next iteration
        current_price = close_p
        
        candles.append({
            'open': round(open_p, 2),
            'high': round(high_p, 2),
            'low': round(low_p, 2),
            'close': round(close_p, 2)
        })
        
    return candles
```

### 2. `generate_mean_reverting`
Generates data that oscillates around the initial mean (`start_price`).

```python
def generate_mean_reverting(n, start_price, volatility):
    """
    Generates n candlesticks that revert towards a mean price (start_price).
    
    Args:
        n (int): Number of candles.
        start_price (float): The mean price around which data oscillates.
        volatility (float): Standard deviation scale for oscillation (e.g., 0.02).
        
    Returns:
        List of dicts containing 'open', 'high', 'low', 'close'.
    """
    candles = []
    current_price = start_price
    
    for _ in range(n):
        # Drift towards mean
        drift = random.uniform(0, 0.1) # Bias slightly up/down randomly but bounded
        
        open_p = current_price + (drift * volatility) - random.gauss(0, current_price * 0.01)
        
        # High/Low spread around Open/Close
        high_noise = abs(random.uniform(current_price * 0.005, current_price * 0.02))
        low_noise = abs(random.uniform(current_price * 0.005, current_price * 0.02))
        
        high_p = max(open_p, current_price) + high_noise
        low_p = min(open_p, current_price) - low_noise
        
        # Close reverts (pull back to mean-ish, but with noise)
        close_p = open_p + random.gauss(0, current_price * 0.05) 
        
        # Ensure OHLC validity
        if open_p > close_p:
            high_p = max(high_p, open_p)
            low_p = min(low_p, close_p)
        else:
            high_p = max(high_p, close_p)
            low_p = min(low_p, open_p)
            
        current_price = close_p
        
        candles.append({
            'open': round(open_p, 2),
            'high': round(high_p, 2),
            'low': round(low_p, 2),
            'close': round(close_p, 2)
        })
        
    return candles
```

### 3. `generate_flash_crash`
Generates data that includes a sudden crash at a specific bar index and then recovers over subsequent bars.

```python
def generate_flash_crash(n, start_price, crash_bar, recovery_bars):
    """
    Generates n candlesticks with a flash crash event.
    
    Args:
        n (int): Number of candles.
        start_price (float): Initial price.
        crash_bar (int): Index (0-based) where the crash occurs. 
                         If crash_bar is None, no crash happens.
        recovery_bars (int): Number of bars for price to recover post-crash.
        
    Returns:
        List of dicts containing 'open', 'high', 'low', 'close'.
    """
    candles = []
    current_price = start_price
    
    # Phase 1: Normal movement before crash
    crash_idx = crash_bar - 1 if crash_bar else None
    
    for i in range(n):
        # Noise
        noise = random.uniform(-current_price * 0.01, current_price * 0.01)
        open_p = current_price + noise
        
        # High/Low spread
        high_noise = abs(random.uniform(current_price * 0.005, current_price * 0.02))
        low_noise = abs(random.uniform(current_price * 0.005, current_price * 0.02))
        
        high_p = max(open_p, current_price) + high_noise
        low_p = min(open_p, current_price) - low_noise
        
        # Logic for specific phases
        if crash_idx is not None and i == crash_idx:
            # CRASH EVENT
            crash_factor = random.uniform(0.90, 0.85) # Drop to ~85-90% of price
            close_p = open_p * crash_factor
            
            # Expand low significantly
            low_p = min(low_p, current_price * crash_factor * 0.95)
            
        elif crash_idx is not None and i > crash_idx:
            if (i - crash_idx) < recovery_bars:
                # RECOVERY PHASE: Force upward movement
                recovery_strength = random.uniform(1.02, 1.05) # Move up 2-5%
                close_p = open_p * recovery_strength
            
                # If recovered enough, revert to normal noise
                if i - crash_idx >= recovery_bars:
                     close_p = open_p + random.gauss(0, current_price * 0.01)
            else:
                 # Normal movement after recovery
                 close_p = open_p + random.gauss(0, current_price * 0.01)
        else:
            # NORMAL MOVEMENT
            close_p = open_p + random.gauss(0, current_price * 0.02)
            
        # Ensure OHLC validity for all candles
        if open_p > close_p:
            high_p = max(high_p, open_p)
            low_p = min(low_p, close_p)
        else:
            high_p = max(high_p, close_p)
            low_p = min(low_p, open_p)
            
        current_price = close_p
        
        candles.append({
            'open': round(open_p, 2),
            'high': round(high_p, 2),
            'low': round(low_p, 2),
            'close': round(close_p, 2)
        })
        
    return candles
```

### Usage Example

You can use these functions to generate distinct datasets. For example:

```python
# Generate Trending Data
trend_data = generate_trending(100, start_price=100, growth_rate=0.005)

# Generate Mean Reverting Data (Mean is 100)
mean_data = generate_mean_reverting(100, start_price=100, volatility=2)

# Generate Flash Crash Data
# Crash occurs at bar index 45 (approx halfway). 
# It takes 20 bars to recover.
crash_data = generate_flash_crash(100, start_price=100, crash_bar=45, recovery_bars=20)
```

### Explanation of Functionality:
*   **`generate_trending`**: Uses a positive drift (`growth_rate`) in the `close_p` calculation. Every candle tries to close higher than it opened slightly over time.
*   **`generate_mean_reverting`**: The price is pulled towards `start_price`. The noise includes a bias that prevents large sustained trends, mimicking a range-bound market or mean-reversion strategy behavior.
*   **`generate_flash_crash`**: This introduces a specific logic block. If the loop reaches `crash_bar`, the `close_p` is multiplied by a factor (e.g., 0.85) to simulate a massive drop, and the `low` is expanded. The next `recovery_bars` force an upward multiplier (`>1.0`) to simulate market stabilization or panic buying ending the crash.

### How to Integrate:
You can plug these functions into your larger project by replacing your existing data loading function with a call to one of these (or a combination), or passing the generated list directly into your analysis pipeline (e.g., training a model, calculating indicators). If you need these inside an `if __name__ == "__main__":` block for immediate testing, I can provide that script.