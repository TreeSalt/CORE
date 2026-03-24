# MISSION: Live Risk Monitor Test Suite
DOMAIN: 06_BENCHMARKING
TYPE: IMPLEMENTATION

## DELIVERABLE
File: 06_BENCHMARKING/tests/02_RISK_MANAGEMENT/test_live_risk_monitor.py

## REQUIREMENTS
- test_drawdown_triggers: verify check_drawdown returns True when limit exceeded
- test_drawdown_safe: verify returns False when within limit
- test_position_limit: verify position limit check works both directions
- test_dead_man_switch_stale: verify returns True when heartbeat is old
- test_dead_man_switch_fresh: verify returns False when heartbeat is recent
- Use pytest, no external calls
- Output valid Python only
