# MISSION: Overnight Range Trap Strategy
DOMAIN: 00_PHYSICS_ENGINE
TYPE: IMPLEMENTATION

## DELIVERABLE
File: 00_PHYSICS_ENGINE/physics_engine/strategies/overnight_range_trap.py

## REQUIREMENTS
- Calculate overnight range (18:00 prev day to 09:30 current)
- Detect breakout of overnight high/low in first 30 min RTH
- Fade if price returns inside range within N bars (default 3)
- generate_signal(bars) -> dict with signal, confidence, entry_price, stop_loss
- No external API calls
- Output valid Python only
