# MISSION: ATR Regime Filter Strategy
DOMAIN: 00_PHYSICS_ENGINE
TYPE: IMPLEMENTATION

## DELIVERABLE
File: 00_PHYSICS_ENGINE/physics_engine/strategies/atr_regime.py

## REQUIREMENTS
- ATRRegimeStrategy class inheriting from Strategy base
- init_params(config): atr_period, regime_lookback, trend_threshold
- on_bar(candle): update ATR and regime state
- get_signal() -> float between -1 and 1
- Only generates signals in trending regimes (uses regime_detector_v2)
- Filters out signals when volatility (ATR) exceeds 2x its rolling average
- Uses math and statistics modules only
- No external calls
- Output valid Python only
