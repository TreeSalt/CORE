# MISSION: Full Predatory Gate Run — All Strategies
DOMAIN: 00_PHYSICS_ENGINE
TASK: run_full_predatory_gate
TYPE: IMPLEMENTATION

## CONTEXT
Run the Predatory Gate (Black Swan stress test) against ALL strategies from E1-E5. Output a comprehensive report showing which strategies survive and which go to the graveyard. Scenarios: COVID March 2020, Flash Crash 2010, Fed Pivot, Gap Down.

## DELIVERABLE
File: scripts/run_full_predatory_gate.py

## REQUIREMENTS
- Discover all strategy files in mantis_core/strategies/
- Run each through 4 stress scenarios
- Track max drawdown per strategy per scenario
- Kill threshold: 15% max drawdown in any scenario
- Output JSON report: strategy_id, scenario, max_dd, status (SURVIVOR/GRAVEYARD)
- Update state/champion_registry.json with survivors
- No external API calls
- Output valid Python only
