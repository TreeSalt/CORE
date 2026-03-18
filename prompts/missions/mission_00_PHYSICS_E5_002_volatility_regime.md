# Mission: E5 Strategy — Volatility Regime Detector

## Domain
00_PHYSICS_ENGINE

## Model Tier
Heavy (27b)

## Description
Generate a trading strategy that classifies market conditions into volatility
regimes (low, normal, high, crisis) and adapts position sizing accordingly.

REQUIREMENTS:
- Uses ATR (Average True Range) and VIX-proxy calculations
- Classifies into 4 regimes with configurable thresholds
- Position size scales inversely with volatility regime
- Must include circuit breaker: if regime = CRISIS, position size = 0
- Must handle missing data gracefully (NaN in price series)

OUTPUT: 00_PHYSICS_ENGINE/strategy_zoo/E5_001_volatility_regime.py
ALLOWED IMPORTS: json, math, statistics, dataclasses, typing, pathlib, datetime
NO EXTERNAL LIBRARIES (no pandas, numpy, scipy — pure stdlib)
TEST: Feed synthetic price series with known volatility transitions. Assert regime changes detected at correct indices. Assert position_size = 0 during crisis regime.

## Acceptance Criteria
- VolatilityRegime enum: LOW, NORMAL, HIGH, CRISIS
- calculate_atr(prices, period=14) returns float
- classify_regime(atr, thresholds) returns VolatilityRegime
- position_size(regime, base_size) returns scaled size, 0 for CRISIS
- Handles NaN values without crashing
- All imports from Python stdlib only
