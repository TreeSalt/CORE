---
DOMAIN: 00_PHYSICS_ENGINE
MODEL: qwen3.5:27b
TIER: heavy
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

from dataclasses import dataclass
import pandas as pd


@dataclass(frozen=True)
class RegimeState:
    regime: str  # TRENDING_UP, TRENDING_DOWN, RANGING, VOLATILE
    atr_value: float
    slope_value: float
    confidence: float


def calculate_atr(prices: pd.Series, window: int) -> float:
    """Calculate Average True Range for the given window."""
    if len(prices) < window:
        return float('nan')
    
    # Calculate true range using price changes as proxy
    price_changes = abs(prices.diff())
    atr_value = price_changes.rolling(window=window).mean().iloc[-1]
    
    return atr_value


def calculate_slope(prices: pd.Series, window: int) -> float:
    """Calculate rolling linear regression slope."""
    if len(prices) < window:
        return 0.0
    
    recent_prices = prices.tail(window).dropna()
    n = len(recent_prices)
    
    if n < 2:
        return 0.0
    
    x = list(range(n))
    y = recent_prices.values
    
    mean_x = sum(x) / n
    mean_y = sum(y) / n
    
    numerator = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
    denominator = sum((x[i] - mean_x) ** 2 for i in range(n))
    
    if denominator == 0:
        return 0.0
    
    return numerator / denominator


def detect_regime(prices: pd.Series, atr_window: int, slope_window: int) -> RegimeState:
    """
    Detect market regime based on ATR and rolling slope.
    
    Args:
        prices: pandas Series of price data
        atr_window: window size for ATR calculation
        slope_window: window size for slope calculation
        
    Returns:
        RegimeState: frozen dataclass with detected regime information
    """
    # Calculate primary signals
    atr_value = calculate_atr(prices, atr_window)
    slope_value = calculate_slope(prices, slope_window)
    
    if pd.isna(atr_value):
        atr_value = 0.0
        
    current_price = prices.iloc[-1] if len(prices) > 0 else 0.0
    normalized_atr = (atr_value / abs(current_price)) if current_price != 0 else 0.0
    
    # Define thresholds for regime classification
    VOLATILITY_THRESHOLD = 0.03  # 3% ATR relative to price indicates volatility
    SLOPE_THRESHOLD = 0.005     # Slope threshold for trending detection
    
    # Determine regime based on signal strength
    if normalized_atr >= VOLATILITY_THRESHOLD:
        regime = "VOLATILE"
        confidence = min(normalized_atr / (2 * VOLATILITY_THRESHOLD), 1.0)
    elif slope_value >= SLOPE_THRESHOLD:
        regime = "TRENDING_UP"
        confidence = min(abs(slope_value) / (SLOPE_THRESHOLD * 2), 1.0)
    elif slope_value <= -SLOPE_THRESHOLD:
        regime = "TRENDING_DOWN"
        confidence = min(abs(slope_value) / (SLOPE_THRESHOLD * 2), 1.0)
    else:
        regime = "RANGING"
        confidence = max(0.5, 1.0 - normalized_atr / VOLATILITY_THRESHOLD)
    
    # Ensure confidence is clamped between 0 and 1
    confidence = min(max(confidence, 0.0), 1.0)
    
    return RegimeState(
        regime=regime,
        atr_value=float(atr_value),
        slope_value=float(slope_value),
        confidence=float(confidence)
    )