---
DOMAIN: 01_DATA_INGESTION
MODEL: qwen3.5:9b
TIER: cruiser
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

Here are the complete Python functions to generate different types of synthetic market data. You can save these in a file (e.g., `market_data_generator.py`) and import them into your project.

```python
import numpy as np

def generate_trending(n, start_price, drift_pct=0.5, noise=1.0):
    """
    Generate market data with positive trend and specified noise.
    
    Parameters:
        n (int) -> Number of bars.
        start_price (float) -> Initial price.
        drift_pct (float) -> Daily drift in percent (e.g., 0.5% means +0.5%).
        noise (float) -> Noise level as a percentage (e.g., 1.0% means std=1%).
        
    Returns:
        prices (list of float).
    """
    prices = [start_price]
    current_price = start_price
    
    # Convert percentages to fractions
    drift_fraction = drift_pct / 100.0
    noise_fraction = noise / 100.0
    
    for _ in range(n - 1):
        change = np.random.normal(drift_fraction, noise_fraction)
        current_price *= (1 + change)
        prices.append(current_price)
    
    return prices

def generate_noise_only(n, start_price, noise=1.0):
    """
    Generate market data with no trend (drift=0).
    
    Parameters:
        n (int) -> Number of bars.
        start_price (float) -> Initial price.
        noise (float) -> Noise level as a percentage.
        
    Returns:
        prices (list of float).
    """
    prices = [start_price]
    current_price = start_price
    
    drift_fraction = 0.0
    noise_fraction = noise / 100.0
    
    for _ in range(n - 1):
        change = np.random.normal(drift_fraction, noise_fraction)
        current_price *= (1 + change)
        prices.append(current_price)
    
    return prices

def generate_volatile(n, start_price, noise=2.0):
    """
    Generate market data with higher volatility (higher noise).
    
    Parameters:
        n (int) -> Number of bars.
        start_price (float) -> Initial price.
        noise (float) -> Noise level as a percentage (default 2.0%).
        
    Returns:
        prices (list of float).
    """
    prices = [start_price]
    current_price = start_price
    
    drift_fraction = 0.0
    noise_fraction = noise / 100.0
    
    for _ in range(n - 1):
        change = np.random.normal(drift_fraction, noise_fraction)
        current_price *= (1 + change)
        prices.append(current_price)
    
    return prices

def generate_happy(n, start_price):
    """
    Generate happy market data with positive trend and default noise.
    
    Parameters:
        n (int) -> Number of bars.
        start_price (float) -> Initial price.
        
    Returns:
        prices (list of float).
    """
    prices = [start_price]
    current_price = start_price
    
    # Default positive drift and default noise for happy market.
    # Using 0.5% drift and 1% noise.
    drift_pct = 0.5
    noise = 1.0
    
    drift_fraction = drift_pct / 100.0
    noise_fraction = noise / 100.0
    
    for _ in range(n - 1):
        change = np.random.normal(drift_fraction, noise_fraction)
        current_price *= (1 + change)
        prices.append(current_price)
    
    return prices
```

### How to Use:

1. **Save** the above code into a file named `market_data_generator.py`.
2. **Import** into your script:
   ```python
   from market_data_generator import generate_trending, generate_happy, generate_noise_only, generate_volatile
   ```
3. **Generate data**:
   ```python
   happy_data = generate_happy(256, 100)
   noisy_data = generate_noise_only(256, 100, noise=2.0)
   trending_data = generate_trending(256, 100, drift_pct=0.3, noise=0.8)
   volatile_data = generate_volatile(256, 100, noise=3.0)
   ```

This provides you with flexible tools to simulate different market conditions for your trading algorithm or analysis tasks.