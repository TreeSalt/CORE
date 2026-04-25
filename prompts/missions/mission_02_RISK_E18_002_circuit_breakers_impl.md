# MISSION: mantis_risk_circuit_breakers_impl
TYPE: IMPLEMENTATION
MISSION_ID: 02_RISK_E18_002_circuit_breakers_impl

## DELIVERABLE
File: mantis_core/risk/circuit_breakers.py

## INTERFACE CONTRACT
### Class: CircuitBreaker
Methods: check(state) -> bool, trip(reason), reset(sovereign_signature)
### Class: DrawdownBreaker(CircuitBreaker)
### Class: DailyLossBreaker(CircuitBreaker)
### Class: PositionConcentrationBreaker(CircuitBreaker)
