# MISSION: Signal Aggregator
DOMAIN: 00_PHYSICS_ENGINE
TYPE: IMPLEMENTATION

## DELIVERABLE
File: 00_PHYSICS_ENGINE/physics_engine/signal_aggregator.py

## REQUIREMENTS
- SignalAggregator class
- add_signal(name, value, weight) -> None: register a signal with its weight
- get_composite(method) -> float: weighted average or majority vote of all registered signals
- get_conviction() -> float between 0 and 1: agreement level among signals
- reset() -> None: clear all signals for next bar
- Pure in-memory, no external calls
- Output valid Python only
