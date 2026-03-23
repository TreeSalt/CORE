# MISSION: Keltner Channel Squeeze Strategy
DOMAIN: 00_PHYSICS_ENGINE
TYPE: IMPLEMENTATION

## DELIVERABLE
File: 00_PHYSICS_ENGINE/physics_engine/strategies/keltner_squeeze.py

## REQUIREMENTS
- Detect when Bollinger Bands contract inside Keltner Channels (squeeze)
- Track squeeze duration (bars)
- Signal on squeeze release: breakout direction = trade direction
- Configurable BB period (20), KC period (20), KC multiplier (1.5)
- generate_signal(bars) -> dict with signal, confidence, entry_price, stop_loss
- No external API calls
- Output valid Python only
