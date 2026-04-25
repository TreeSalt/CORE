# MISSION: regime_detector_v2
TYPE: IMPLEMENTATION
MISSION_ID: 00_PHYSICS_E16_001_regime_detector_v2

## CONTEXT
The original regime_detector escalated repeatedly due to Ollama 500
errors during heavy tier dispatch. With auto_deploy_v2 fixed and the
E14 gates in place, retry on heavy tier.

The original brief is at prompts/missions/mission_00_PHYSICS_E13_001_regime_detector.md.
Follow it.

## DELIVERABLE
File: mantis_core/physics/regime_detector.py

## SUMMARY OF REQUIREMENTS
- Detect market regime: TRENDING_UP, TRENDING_DOWN, RANGING, VOLATILE
- Use ATR and rolling slope as primary signals
- Configurable lookback windows
- Frozen dataclass for RegimeState
- Pure function: detect_regime(prices: pd.Series, atr_window: int, slope_window: int) -> RegimeState
