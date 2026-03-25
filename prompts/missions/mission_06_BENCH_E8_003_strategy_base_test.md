# MISSION: Strategy Base Class Test Suite
DOMAIN: 06_BENCHMARKING
TYPE: IMPLEMENTATION

## DELIVERABLE
File: 06_BENCHMARKING/tests/00_PHYSICS_ENGINE/test_strategy_base.py

## REQUIREMENTS
- test_cannot_instantiate_abstract: verify Strategy ABC cannot be directly instantiated
- test_concrete_strategy_works: create a minimal concrete subclass, verify it instantiates
- test_position_size_returns_float: verify position_size returns a positive float
- test_should_exit_stop_loss: verify exit triggers when price hits stop loss
- Use pytest
- No external calls
- Output valid Python only
