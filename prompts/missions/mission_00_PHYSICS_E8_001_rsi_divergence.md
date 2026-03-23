# MISSION: RSI Divergence Strategy
DOMAIN: 00_PHYSICS_ENGINE
TYPE: IMPLEMENTATION

## CONTEXT
Detect RSI divergences — price makes new highs/lows but RSI does not confirm. Mean-reversion signal for ranging markets.

## DELIVERABLE
File: 00_PHYSICS_ENGINE/physics_engine/strategies/rsi_divergence.py

## REQUIREMENTS
- Detect bullish divergence (price lower low, RSI higher low)
- Detect bearish divergence (price higher high, RSI lower high)
- Configurable RSI period (default 14), lookback (default 20 bars)
- generate_signal(bars) -> dict with signal, confidence, entry_price, stop_loss
- No external API calls
- Output valid Python only
