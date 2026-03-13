---
DOMAIN: 00_PHYSICS_ENGINE
MODEL: qwen2.5-coder:32b
TIER: heavy
TYPE: IMPLEMENTATION
STATUS: RATIFIED
---

Certainly! Below is a proposal for implementing the `ZOO_E2_001` variant within the `antigravity_harness` framework, adhering to all specified constraints and guidelines.

```python
# File: antigravity_harness/strategies/lab/v_zoo_zoo_e2_001/v_zoo_zoo_e2_001.py

import pandas as pd
import numpy as np
from antigravity_harness.strategies.base import Strategy

class V_Zoo_Zoo_E2_001(Strategy):
    def prepare_data(self, df, params, intelligence=None, vector_cache=None) -> pd.DataFrame:
        # Ensure all necessary columns are present
        required_columns = ['close', 'high', 'low']
        for column in required_columns:
            if column not in df.columns:
                raise ValueError(f"Missing required column: {column}")

        # Calculate typical price
        df.loc[:, 'typical_price'] = (df.loc[:, 'high'] + df.loc[:, 'low'] + df.loc[:, 'close']) / 3

        # Calculate the 20-day standard deviation of the typical price
        window = 20
        df.loc[:, 'std_dev'] = df.loc[:, 'typical_price'].rolling(window=window).std()

        # Calculate the Bollinger Bands
        num_std_dev = 2
        df.loc[:, 'middle_band'] = df.loc[:, 'typical_price'].rolling(window=window).mean()
        df.loc[:, 'upper_band'] = df.loc[:, 'middle_band'] + (df.loc[:, 'std_dev'] * num_std_dev)
        df.loc[:, 'lower_band'] = df.loc[:, 'middle_band'] - (df.loc[:, 'std_dev'] * num_std_dev)

        # Calculate the bandwidth
        df.loc[:, 'bandwidth'] = df.loc[:, 'upper_band'] - df.loc[:, 'lower_band']

        # Calculate the 6-month low of the bandwidth
        lookback_period = 180  # Assuming 180 trading days in 6 months
        df.loc[:, 'bandwidth_6m_low'] = df.loc[:, 'bandwidth'].rolling(window=lookback_period).min()

        # Calculate the entry signal
        df.loc[:, 'entry_signal'] = (df.loc[:, 'bandwidth'] == df.loc[:, 'bandwidth_6m_low'])

        # Calculate the ATR (Average True Range)
        df.loc[:, 'true_range'] = np.maximum.reduce([
            df.loc[:, 'high'] - df.loc[:, 'low'],
            np.abs(df.loc[:, 'high'] - df.loc[:, 'close'].shift()),
            np.abs(df.loc[:, 'low'] - df.loc[:, 'close'].shift())
        ])
        df.loc[:, 'ATR'] = df.loc[:, 'true_range'].rolling(window=window).mean()

        # Calculate the exit signal (bands expand 2x)
        df.loc[:, 'exit_signal'] = (df.loc[:, 'bandwidth'] > (df.loc[:, 'bandwidth_6m_low'] * 2))

        # Drop intermediate columns
        df.drop(columns=['typical_price', 'std_dev', 'middle_band', 'upper_band', 'lower_band', 'true_range', 'bandwidth_6m_low'], inplace=True)

        # Ensure signals are booleans
        df.loc[:, 'entry_signal'] = df.loc[:, 'entry_signal'].astype(bool)
        df.loc[:, 'exit_signal'] = df.loc[:, 'exit_signal'].astype(bool)

        return df
```

### Key Points:
1. **Typical Price Calculation**: Used to smooth out the price data.
2. **Bollinger Bands**: Calculated using a 20-day window and 2 standard deviations.
3. **Bandwidth**: Calculated as the difference between the upper and lower Bollinger Bands.
4. **6-Month Low of Bandwidth**: Used to detect when the bandwidth contracts to its lowest point in the last 6 months.
5. **Entry Signal**: Triggered when the bandwidth hits its 6-month low.
6. **ATR (Average True Range)**: Calculated to measure market volatility.
7. **Exit Signal**: Triggered when the bandwidth expands to twice its 6-month low.
8. **Constraints**: All constraints are adhered to, including the use of `.loc[]` for indexing and no chained indexing.

This code should be placed in the specified file and should work within the `antigravity_harness` framework as per the provided guidelines.