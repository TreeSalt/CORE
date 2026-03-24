# MISSION: Execution Simulator
DOMAIN: 00_PHYSICS_ENGINE
TYPE: IMPLEMENTATION

## DELIVERABLE
File: 00_PHYSICS_ENGINE/physics_engine/execution_simulator.py

## REQUIREMENTS
- simulate_fill(order_price, market_price, slippage_bps, partial_fill_pct) -> dict
- Returns: fill_price, filled_qty, slippage_cost, partial flag
- simulate_latency(base_ms, jitter_ms) -> float: simulated execution delay in ms
- Model slippage as proportional to order size relative to volume
- All parameters are function arguments with sensible defaults
- No external calls
- Output valid Python only
