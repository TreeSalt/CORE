# MISSION: Predatory Gate Runner — Execute Stress Tests
DOMAIN: 06_BENCHMARKING
TASK: implement_predatory_gate_runner
TYPE: IMPLEMENTATION
VERSION: 1.0

## CONTEXT
The Predatory Gate module exists (ratified). Now we need a runner script
that executes it against all Zoo strategies and produces the results.

## BLUEPRINT
Create a script that:
1. Discovers all Zoo strategy proposals in 08_IMPLEMENTATION_NOTES/
2. Extracts the Python class from each proposal
3. Instantiates each strategy
4. Runs it through the Predatory Gate's 4 scenarios (COVID, Flash Crash, Fed Pivot, Gap Down)
5. Writes PREDATORY_GATE_REPORT.json with per-strategy, per-scenario results
6. Strategies that breach 15% max drawdown → writes GRAVEYARD.md entry
7. Survivors listed in state/predatory_gate_survivors.json

## DELIVERABLE
File: scripts/run_predatory_gate.py

## CONSTRAINTS
- Must be runnable as: python3 scripts/run_predatory_gate.py
- Read drawdown threshold from CHECKPOINTS.yaml
- Write results to state/ directory
- No external API calls
- Output valid Python only
