# MISSION: VWAP Standard Deviation Bands Strategy
DOMAIN: 00_PHYSICS_ENGINE
TYPE: IMPLEMENTATION

## DELIVERABLE
File: 00_PHYSICS_ENGINE/physics_engine/strategies/vwap_bands.py

## REQUIREMENTS
- Calculate intraday VWAP and +/- 1, 2, 3 standard deviation bands
- Long when price touches -2SD band and reverses toward VWAP
- Short when price touches +2SD band and reverses toward VWAP
- Reset VWAP at session open (configurable)
- generate_signal(bars) -> dict with signal, confidence, entry_price, stop_loss
- No external API calls
- Output valid Python only
