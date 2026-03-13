# MISSION: Predatory Gate — Black Swan Stress Test
DOMAIN: 00_PHYSICS_ENGINE
TASK: implement_predatory_gate
TYPE: IMPLEMENTATION
VERSION: 1.0

## CONTEXT
Per ROADMAP v2.0, before any Zoo strategy enters the live paper queue, it must
survive the Predatory Gate: a stress test against extreme historical scenarios.

## BLUEPRINT
Create a module that:
1. Loads a strategy (via ZooStrategyAdapter)
2. Runs it against synthetically generated extreme scenarios:
   - COVID crash: 5 days of -5% daily drops, expanding ATR
   - Flash Crash: 200 bars cascading -0.5% per bar, then V-recovery
   - Fed Pivot: 3 intraday reversals of 2%+ each
   - Gap Down: overnight gap of -3%, then slow recovery
3. Computes max drawdown for each scenario
4. PASS/FAIL against CHECKPOINTS.yaml max_drawdown_pct (15%)
5. Writes PREDATORY_GATE_REPORT.json
6. Failed strategies get automatic GRAVEYARD entry

## DELIVERABLE
File: antigravity_harness/gates/predatory_gate.py

## CONSTRAINTS
- Generate scenarios from parameters (no external data files)
- Read drawdown threshold from CHECKPOINTS.yaml
- No external API calls
- Output valid Python only
