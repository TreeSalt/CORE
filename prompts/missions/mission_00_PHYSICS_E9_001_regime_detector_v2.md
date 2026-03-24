# MISSION: Regime Detector v2
DOMAIN: 00_PHYSICS_ENGINE
TYPE: IMPLEMENTATION

## DELIVERABLE
File: 00_PHYSICS_ENGINE/physics_engine/regime_detector_v2.py

## REQUIREMENTS
- detect_regime(candles, lookback) -> str: returns "trending_up", "trending_down", "mean_reverting", "volatile", or "unknown"
- Uses rolling volatility (std of returns) and rolling momentum (rate of change)
- Regime thresholds are function parameters, not hardcoded
- get_regime_history(candles, lookback, window) -> list of regime strings
- No external calls, no imports beyond stdlib and math
- Output valid Python only
