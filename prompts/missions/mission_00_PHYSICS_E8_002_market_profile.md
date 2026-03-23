# MISSION: Market Profile Value Area Strategy
DOMAIN: 00_PHYSICS_ENGINE
TYPE: IMPLEMENTATION

## DELIVERABLE
File: 00_PHYSICS_ENGINE/physics_engine/strategies/market_profile_value.py

## REQUIREMENTS
- Calculate TPO profile from OHLCV bars
- Identify Value Area High, Value Area Low, Point of Control
- Long when price dips below VAL and reverses; short above VAH
- Configurable session window (default RTH 9:30-16:00)
- generate_signal(bars) -> dict with signal, confidence, entry_price, stop_loss
- No external API calls
- Output valid Python only
