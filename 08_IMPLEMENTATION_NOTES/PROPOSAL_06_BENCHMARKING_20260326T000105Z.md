---
DOMAIN: 06_BENCHMARKING
MODEL: qwen3.5:4b
TIER: sprinter
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

```python
import pandas as pd
import numpy as np

def calculate_bollinger_bands(prices: pd.Series, window: int = 20) -> pd.DataFrame:
    """
    Calculates standard Bollinger Bands from input price series.
    Uses mock logic for testing without external API access or credentials.
    """
    rolling_mean = prices.rolling(window=window).mean()
    rolling_std = prices.rolling(window=window).std()
    
    upper_band = rolling_mean + (2 * rolling_std)
    lower_band = rolling_mean - (2 * rolling_std)
    
    return pd.DataFrame({
        'Upper Band': upper_band,
        'Middle Band': rolling_mean,
        'Lower Band': lower_band
    })

def validate_bollinger_logic(prices: pd.Series, window: int) -> bool:
    """
    Validates the calculation logic against expected data structures.
    No writes to GOVERNANCE or use of credentials allowed.
    """
    try:
        result = calculate_bollinger_bands(prices, window=window)
        
        # Check for NaN values in lower bands (common edge case test)
        assert all(pd.notna(result['Lower Band'].iloc[i]) for i in range(len(result)))
        
        # Ensure upper and middle bands are close enough to be valid ranges
        assert (result['Upper Band'] > result['Middle Band']).all()
        
        return True
    except Exception as e:
        return False

if __name__ == "__main__":
    # Generate safe mock data for testing
    np.random.seed(42)
    test_data = pd.Series(np.random.randn(50) * 10 + 100)
    
    is_valid = validate_bollinger_logic(test_data, window=5)
    
    if is_valid:
        print("Bollinger Band Logic Test Passed")
    else:
        print("Bollinger Band Logic Test Failed")
```