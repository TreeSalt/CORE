# MISSION: mantis_signal_aggregator_impl
TYPE: IMPLEMENTATION
MISSION_ID: 00_PHYSICS_E18_002_signal_aggregator_impl

## DELIVERABLE
File: mantis_core/physics/signal_aggregator.py

## INTERFACE CONTRACT
### Function: aggregate_signals(regime_state, trend_signal_value, weights) -> AggregatedSignal
### Dataclass: AggregatedSignal (frozen) with fields: direction, strength, confidence, regime
