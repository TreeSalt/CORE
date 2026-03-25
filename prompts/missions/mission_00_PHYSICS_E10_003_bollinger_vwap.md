# MISSION: Bollinger-VWAP Hybrid Strategy
DOMAIN: 00_PHYSICS_ENGINE
TYPE: IMPLEMENTATION

## DELIVERABLE
File: 00_PHYSICS_ENGINE/physics_engine/strategies/bollinger_vwap.py

## REQUIREMENTS
- BollingerVWAPStrategy class inheriting from Strategy base
- init_params(config): bollinger_period, bollinger_std, vwap_lookback
- on_bar(candle): update internal state with new candle data
- get_signal() -> float between -1 and 1: negative is sell, positive is buy
- Buy signal when price below lower bollinger band AND below VWAP
- Sell signal when price above upper bollinger band AND above VWAP
- Uses math and statistics modules only
- No external calls
- Output valid Python only
