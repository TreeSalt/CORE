# MISSION: Strategy Base Class
DOMAIN: 00_PHYSICS_ENGINE
TYPE: IMPLEMENTATION

## DELIVERABLE
File: 00_PHYSICS_ENGINE/physics_engine/strategy_base.py

## REQUIREMENTS
- Strategy abstract base class (ABC)
- Abstract methods: init_params(config), on_bar(candle), get_signal(), get_state()
- position_size(equity, risk_pct) -> float: Kelly-inspired position sizing
- should_enter(signal, regime) -> bool: combine signal with regime filter
- should_exit(position, candle, stop_loss, take_profit) -> bool
- All methods are pure functions or use instance state only
- No external calls, no imports beyond stdlib, math, and abc
- Output valid Python only
