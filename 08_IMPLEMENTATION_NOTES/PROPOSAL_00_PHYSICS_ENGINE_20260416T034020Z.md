---
DOMAIN: 00_PHYSICS_ENGINE
MODEL: qwen3.5:27b
TIER: heavy
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

```python
from dataclasses import dataclass
from enum import Enum, auto
import pandas as pd
import numpy as np


class MarketRegime(Enum):
    """Market regime classification."""
    TRENDING_UP = auto()
    TRENDING_DOWN = auto()
    RANGING = auto()
    VOLATILE = auto()


@dataclass(frozen=True)
class RegimeState:
    """Frozen dataclass representing detected market regime state."""
    regime: MarketRegime
    atr_value: float
    slope_value: float
    volatility_ratio: float
    confidence: float


def detect_regime(
    prices: pd.Series,
    atr_window: int = 14,
    slope_window: int = 20
) -> RegimeState:
    """
    Detect market regime using ATR and rolling slope analysis.

    Args:
        prices: Pandas Series of price data
        atr_window: Lookback window for ATR calculation (default 14)
        slope_window: Lookback window for slope calculation (default 20)

    Returns:
        RegimeState object with regime classification and metrics
    """
    if prices.empty or len(prices) < max(atr_window, slope_window):
        return RegimeState(
            regime=MarketRegime.RANGING,
            atr_value=0.0,
            slope_value=0.0,
            volatility_ratio=0.0,
            confidence=0.0
        )

    prices = prices.dropna()

    price_changes = np.abs(prices.diff()).rolling(window=atr_window).mean().iloc[-1]
    atr_value = float(price_changes)

    recent_prices = prices.tail(slope_window).values.astype(float)
    n_periods = len(recent_prices)
    x = np.arange(n_periods)

    if n_periods < 2:
        slope_value = 0.0
        r_squared = 0.0
    else:
        mean_x, mean_y = np.mean(x), np.mean(recent_prices)
        numerator = np.sum((x - mean_x) * (recent_prices - mean_y))
        denominator = np.sqrt(np.sum((x - mean_x)**2) * np.sum((recent_prices - mean_y)**2))
        slope_value = float(numerator / denominator if denominator != 0 else 0.0)

        corr_squared = numerator**2 / (np.sum((x - mean_x)**2) * np.sum((recent_prices - mean_y)**2))
        r_squared = float(corr_squared) if denominator != 0 else 0.0

    current_price = prices.iloc[-1]
    normalized_slope = slope_value / current_price if current_price > 0 else 0.0

    rolling_std = np.std(recent_prices)
    volatility_ratio = float(rolling_std / atr_value if atr_value > 0 else 0.0)

    price_mean = recent_prices.mean()
    high_vol_threshold = atr_value / price_mean * 100 if price_mean > 0 else 0
    slope_threshold = 1e-4

    if high_vol_threshold > 2.0:
        regime = MarketRegime.VOLATILE
        confidence = min(high_vol_threshold / 4.0, 1.0)
    elif abs(normalized_slope) > slope_threshold:
        if normalized_slope > 0:
            regime = MarketRegime.TRENDING_UP
        else:
            regime = MarketRegime.TRENDING_DOWN
        confidence = min(abs(r_squared), 1.0)
    else:
        regime = MarketRegime.RANGING
        confidence = 1.0 - abs(r_squared) if r_squared >= 0 else 0.5

    return RegimeState(
        regime=regime,
        atr_value=float(atr_value),
        slope_value=float(normalized_slope * 100),
        volatility_ratio=float(volatility_ratio),
        confidence=float(confidence)
    )
```