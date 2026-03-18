# Mission: E5 Graveyard Analysis — Extract Anti-Patterns from E1-E4 Failures

## Domain
00_PHYSICS_ENGINE

## Model Tier
Heavy (27b)

## Description
Analyze the graveyard of failed strategies from epochs E1 through E4.
Extract concrete anti-patterns that E5 strategies must avoid.

Known survivors from prior epochs:
- Bollinger Band strategy: 0.9% max drawdown (E2 survivor)
- VWAP strategy: 0.0% max drawdown (E2 survivor)

Known failure modes (from Predatory Gate):
- E1 strategies all killed by code bugs (AST failures, wrong instrument physics)
- E3/E4 strategies pending test but built on E1/E2 lessons

OUTPUT: 00_PHYSICS_ENGINE/strategy_zoo/E5_GRAVEYARD_ANALYSIS.md
ALLOWED IMPORTS: None (pure Markdown analysis)
TEST: File exists, contains at least 10 anti-patterns, references specific failed strategy names.

## Acceptance Criteria
- Lists at least 10 concrete anti-patterns with examples
- References specific failed strategies by name
- Categorizes failures: code bugs, logic errors, risk management, instrument physics
- Provides positive examples from Bollinger and VWAP survivors
- Ends with E5 design principles derived from the analysis
