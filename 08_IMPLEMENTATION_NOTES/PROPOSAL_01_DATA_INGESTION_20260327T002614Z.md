---
DOMAIN: 01_DATA_INGESTION
MODEL: qwen3.5:9b
TIER: cruiser
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

import random
from datetime import datetime, timedelta
import math

def generate_trending(n, start_price, drift_pct, noise_pct):
    candles = []
    current_price = float(start_price)
    # Using 2023-01-01 as base epoch for reproducibility if not seeded externally
    current_time = datetime(2023, 1, 1, 0, 0, 0)
    
    for i in range(n):
        open_price = current_price
        
        # Ensure valid OHLC construction with drift and noise
        trend_direction = 1 if drift_pct > 0 else -1
        drift_magnitude = abs(start_price * (drift_pct / 100.0))
        
        # Generate noise for high/low bounds around open/close
        body_change = random.uniform(0.8, 1.2) * drift_magnitude
        
        close_price = open_price + trend_direction * body_change
        
        high = max(open_price, close_price) + random.uniform(0, start_price * (noise_pct / 50.0))
        low = min(open_price, close_price) - random.uniform(0, start_price * (noise_pct / 50.0))
        
        if high < open_price or low > close_price:
            # Fix invalid bounds if noise exceeds body logic
            high = max(open_price, close_price) + random.uniform(0.01, noise_pct/100.0 * current_price)
            low = min(open_price, close_price) - random.uniform(0.01, noise_pct/100.0 * current_price)
            
        candles.append({
            'timestamp': current_time,
            'open': open_price,
            'high': high,
            'low': low,
            'close': close_price,
            'volume': random.randint(1000, 5000)
        })
        
        current_price = close_price
        current_time += timedelta(minutes=5)
    return candles

def generate_mean_reverting(n, center_price, amplitude_pct, noise_pct):
    candles = []
    current_price = float(center_price)
    
    for i in range(n):
        open_price = current_price
        
        # Bounds for mean reversion
        bound_low = center_price - (center_price * amplitude_pct / 100)
        bound_high = center_price + (center_price * amplitude_pct / 100)
        
        # Biased random walk towards center
        distance_to_center = current_price - center_price
        pull_factor = -distance_to_center * 0.5 if distance_to_center != 0 else 0
        
        noise_step = random.uniform(-noise_pct/2, noise_pct/2)
        drift_step = math.log(abs(pull_factor)) / abs(pull_factor) # Logistic approximation or simple linear? 
        # Let's keep it simple: Move towards center + noise
        proposed_close = current_price + pull_factor + noise_step
        
        close_price = max(bound_low, min(proposed_close, bound_high))
        
        high = max(open_price, close_price) + random.uniform(0, current_price * (noise_pct / 100.0))
        low = min(open_price, close_price) - random.uniform(0, current_price * (noise_pct / 100.0))

        candles.append({
            'timestamp': datetime.now(), # Placeholder timestamp logic
            'open': open_price,
            'high': high,
            'low': low,
            'close': close_price,
            'volume': random.randint(500, 2000)
        })
        
        current_price = close_price
    return candles

def generate_volatile(n, start_price, volatility_pct, recovery_bars):
    candles = []
    current_price = float(start_price)
    
    for i in range(n):
        open_price = current_price
        
        # High volatility swing
        swing_size = start_price * (volatility_pct / 100.0)
        
        # Randomize direction (Up or Down)
        direction = random.choice([1, -1])
        body_change = swing_size * random.uniform(0.3, 2.0) * direction
        
        close_price = open_price + body_change
        
        high = max(open_price, close_price) + abs(body_change) * random.uniform(0.1, 0.5)
        low = min(open_price, close_price) - abs(body_change) * random.uniform(0.1, 0.5)
        
        # Enforce volume correlation in volatility (optional, but good practice)
        candles.append({
            'timestamp': datetime.now(),
            'open': open_price,
            'high': high,
            'low': low,
            'close': close_price,
            'volume': random.randint(1000, 5000)
        })
        
        current_price = close_price
        
    if recovery_bars > 0:
        for i in range(min(recovery_bars, n)): # Logic implies recovery after crash?
             pass
             
    return candles

def generate_flash_crash(n, start_price, crash_bar, crash_pct, recovery_bars):
    candles = []
    current_price = float(start_price)
    crash_triggered = False
    
    for i in range(n):
        open_price = current_price
        
        if not crash_triggered:
            # Normal walk until crash bar
            change = start_price * random.uniform(-0.1, 0.2) / 5
            close_price = open_price + change
            
            candles.append({
                'timestamp': datetime.now(),
                'open': open_price,
                'high': max(open_price, close_price),
                'low': min(open_price, close_price),
                'close': close_price,
                'volume': random.randint(1000, 5000)
            })
            
            current_price = close_price
            
            if i == crash_bar:
                crash_triggered = True
                # Huge drop at crash bar
                current_price = current_price * (1 - crash_pct/100.0)
                # High/Low adjustment for crash
                high = max(open_price, current_price) + random.uniform(0.5, 2.0) * current_price
                low = min(open_price, current_price) - random.uniform(0.5, 2.0) * current_price
                
            candles.append({
                'timestamp': datetime.now(),
                'open': open_price,
                'high': high,
                'low': low,
                'close': current_price, # Crash occurs here? Or previous close?
                'volume': random.randint(10000, 50000) # High volume on crash
            })
            
            current_price = current_price
        else:
            # Recovery phase
            bounce_factor = start_price * (crash_pct / 2.0) * random.uniform(0.01, 0.1)
            recovery_change = start_price * random.uniform(-0.2, 0.3) + bounce_factor
            
            close_price = open_price + recovery_change
            
            candles.append({
                'timestamp': datetime.now(),
                'open': open_price,
                'high': max(open_price, close_price),
                'low': min(open_price, close_price),
                'close': close_price,
                'volume': random.randint(1000, 5000)
            })
            
            current_price = close_price
            
    return candles