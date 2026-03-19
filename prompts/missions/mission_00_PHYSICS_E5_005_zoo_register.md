# Mission: 00_PHYSICS_E5_005_zoo_register

## Domain
00_PHYSICS_ENGINE

## Model Tier
Sprint (9b)

## Description
Register the three E5 strategies into the strategy zoo directory.

REQUIREMENTS:
1. Copy or move the E5 strategy files into 00_PHYSICS_ENGINE/strategy_zoo/
2. Ensure each file has proper module docstring
3. Create 00_PHYSICS_ENGINE/strategy_zoo/__init__.py that imports all strategies
4. Create 00_PHYSICS_ENGINE/strategy_zoo/REGISTRY.json listing all strategies with metadata

The three E5 strategies are:
- E5_001_volatility_regime.py
- E5_002_mean_reversion.py  
- E5_003_momentum_breakout.py

These were generated in a prior factory batch and exist as proposals.

ALLOWED IMPORTS: json, pathlib
OUTPUT: 00_PHYSICS_ENGINE/strategy_zoo/ directory with strategies and registry
TEST: Assert REGISTRY.json contains 3 entries. Assert __init__.py imports all three.
