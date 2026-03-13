---
DOMAIN: 00_PHYSICS_ENGINE
MODEL: qwen2.5-coder:32b
TIER: heavy
TYPE: IMPLEMENTATION
STATUS: RATIFIED
---

Certainly! Below is a Python code proposal for the `ZOO_E2_004` strategy that adheres to the provided constraints and requirements. This code is intended to be placed in the file `antigravity_harness/strategies/lab/v_zoo_zoo_e2_004/v_zoo_zoo_e2_004.py`.

```python
import pandas as pd

class V_ZOO_ZOO_E2_004(antigravity_harness.strategies.base.Strategy):
    def prepare_data(self, df, params, intelligence=None, vector_cache=None) -> pd.DataFrame:
        # Calculate the 20-bar average volume
        df.loc[:, 'avg_volume_20'] = df['volume'].rolling(window=20).mean()
        
        # Calculate the 20-bar ATR (Average True Range)
        df.loc[:, 'high_low'] = df['high'] - df['low']
        df.loc[:, 'high_close'] = abs(df['high'] - df['close'].shift(1))
        df.loc[:, 'low_close'] = abs(df['low'] - df['close'].shift(1))
        df.loc[:, 'tr'] = df[['high_low', 'high_close', 'low_close']].max(axis=1)
        df.loc[:, 'ATR'] = df['tr'].rolling(window=20).mean()
        
        # Identify volume spikes (volume exceeds 3x 20-bar average)
        df.loc[:, 'volume_spike'] = (df['volume'] > 3 * df['avg_volume_20'])
        
        # Identify new price highs
        df.loc[:, 'new_high'] = (df['close'] > df['close'].rolling(window=20).max())
        
        # Generate entry signal: SHORT when volume spikes and new high is made
        df.loc[:, 'entry_signal'] = (df['volume_spike'] & df['new_high'])
        
        # Generate exit signal: None specified, so set to False
        df.loc[:, 'exit_signal'] = False
        
        # Clean up intermediate columns if necessary
        df.drop(columns=['high_low', 'high_close', 'low_close', 'tr', 'avg_volume_20'], inplace=True)
        
        return df
```

### Explanation:
1. **Volume Calculation**:
   - The `avg_volume_20` column is computed using a 20-bar rolling mean of the `volume` column.
   
2. **ATR Calculation**:
   - The True Range (`tr`) is calculated as the maximum of three values: the difference between high and low, the absolute difference between high and the previous close, and the absolute difference between low and the previous close.
   - The `ATR` is then computed as the 20-bar rolling mean of the True Range.

3. **Volume Spike Detection**:
   - The `volume_spike` column identifies bars where the volume exceeds three times the 20-bar average volume.

4. **New High Detection**:
   - The `new_high` column identifies bars where the closing price is higher than the highest closing price in the past 20 bars.

5. **Entry Signal**:
   - The `entry_signal` column is set to `True` when both a volume spike and a new high occur simultaneously.

6. **Exit Signal**:
   - The `exit_signal` column is set to `False` as no specific exit condition is provided.

7. **Intermediate Column Cleanup**:
   - Intermediate columns used in calculations are dropped to keep the DataFrame clean.

This code ensures that all constraints are respected, including the use of `.loc[]` for DataFrame indexing, no chained indexing, and no external libraries like `talib`.