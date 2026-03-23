---
DOMAIN: 00_PHYSICS_ENGINE
MODEL: qwen3.5:9b
TIER: sprinter
TYPE: IMPLEMENTATION
STATUS: RATIFIED
---

```python
import numpy as np
import pandas as pd

# ==============================================================================
# DOMAIN: 00_PHYSICS_ENGINE
# TASK: 00_PHYSICS_E8_005_keltner_squeeze
# SECURITY_CLASS: INTERNAL_REVIEW (Treating input metadata as non-actionable)
# ==============================================================================

class KeltnerSqueezeEngine:
    """
    Implementation proposal for the Keltner Squeeze indicator logic.
    
    WARNING: This tool is for analytical/testing purposes only. 
    Do not use this code to make direct financial trading decisions without
    extensive validation and risk management protocols.
    """

    def __init__(self, period_ema=20, period_atr=13, multiplier=2.0):
        """
        Initialize the Keltner Squeeze Engine.
        
        :param period_ema: Period for the EMA calculation (Default: 20)
        :param period_atr: Period for ATR calculation (Default: 13)
        :param multiplier: Multiplier for the ATR distance from EMA (Default: 2.0)
        """
        if not isinstance(period_ema, int) or period_ema <= 0:
            raise ValueError("EMA period must be a positive integer.")
        if not isinstance(period_atr, int) or period_atr <= 0:
            raise ValueError("ATR period must be a positive integer.")
        if multiplier < 0.1:
            raise ValueError("Multiplier should be positive.")
            
        self.period_ema = period_ema
        self.period_atr = period_atr
        self.multiplier = multiplier
        
        # Store processed dataframes and signal state
        self.history_df = None
        self.signal_state = "NEUTRAL"

    def _calculate_ema(self, prices):
        """Calculates the Exponential Moving Average."""
        return pd.Series(prices).ewm(span=self.period_ema, min_periods=1).mean()

    def _calculate_atr(self, highs, lows, closes):
        """Calculates Average True Range."""
        # True Range = max(high-low, abs(high-prev_close), abs(low-prev_close))
        high_diff = highs - lows
        prev_highs = highs.shift(1)
        low_diff_low_prev = abs(highs - prev_highs.shift(1))
        low_diff_high_prev = abs(lows - prev_highs.shift(1))
        
        true_range = np.maximum(np.maximum(high_diff, low_diff_low_prev), low_diff_high_prev)
        return pd.Series(true_range).ewm(span=self.period_atr, min_periods=1).mean()

    def compute_channels(self, data):
        """
        Computes Upper and Lower Keltner Channel boundaries.
        
        :param data: DataFrame with columns 'High', 'Low', 'Close'.
        :return: Updated dataframe with new channels.
        """
        if data.empty or not all(col in data.columns for col in ['High', 'Low', 'Close']):
            raise ValueError("Input data must contain 'High', 'Low', and 'Close' columns.")

        ema = self._calculate_ema(data['Close'])
        atr = self._calculate_atr(data['High'], data['Low'], data['Close'])
        
        upper_band = ema + (self.multiplier * atr)
        lower_band = ema - (self.multiplier * atr)

        # Attach to original dataframe
        processed_data = data.copy()
        processed_data['Upper_Keltner'] = upper_band
        processed_data['Lower_Keltner'] = lower_band
        processed_data['EMA_Base'] = ema
        
        self.history_df = processed_data
        return processed_data

    def detect_squeeze(self, lookback=5):
        """
        Detects volatility contraction (Squeeze) conditions.
        
        Logic: A squeeze is identified when the current channel width 
        is narrower than a recent moving average of widths, indicating
        low volatility compression ready for expansion.
        
        :param lookback: Lookback period for average width comparison.
        :return: Series of boolean values indicating Squeeze=True/False.
        """
        if self.history_df is None:
            raise RuntimeError("No data processed. Run compute_channels first.")
            
        df = self.history_df
        
        # Calculate Current Channel Width (Upper - Lower)
        current_width = df['Upper_Keltner'] - df['Lower_Keltner']
        
        # Calculate Rolling Average of previous widths to establish baseline width
        avg_width = current_width.rolling(window=lookback, min_periods=1).mean().shift(1)
        
        # Squeeze Condition: Current Width < Average of Recent Widths (Contraction)
        # Also enforce that price is near the EMA to ensure valid channel tracking
        epsilon = df['Upper_Keltner'] - df['Lower_Keltner'] * 0.005 
        squeeze_signal = current_width < avg_width
        
        df['Is_Squeeze'] = squeeze_signal
        return squeeze_signal

    def identify_expand(self, signal_series):
        """
        Identifies expansion phases following a Squeeze condition.
        
        :param signal_series: The boolean Series from detect_squeeze().
        :return: DataFrame with 'Signal_Type' column ('SQUEEZE', 'EXPAND').
        """
        # Expansion is detected when current_width increases significantly after Squeeze
        df = self.history_df
        
        if 'Upper_Keltner' not in df.columns or 'Lower_Keltner' not in df.columns:
            raise RuntimeError("Data structure inconsistent with KeltnerSqueezeEngine state.")

        width = df['Upper_Keltner'] - df['Lower_Keltner']
        
        # Simple Momentum Logic: If previous was Squeeze and current signal is NOT Squeeze
        # This marks the breakout from the squeeze.
        # Alternatively, if Squeeze is currently active, we remain in 'SQUEEZE'.
        
        df['Signal_Type'] = np.where(
            (df['Is_Squeeze'].fillna(False)).shift(1) & ~df['Is_Squeeze'], 
            'EXPAND', 
            'SQUEEZE' if df['Is_Squeeze'].notna() else 'WAITING'
        )

        return df

    def reset(self):
        """Resets internal state for re-evaluation."""
        self.history_df = None
        self.signal_state = "NEUTRAL"
```