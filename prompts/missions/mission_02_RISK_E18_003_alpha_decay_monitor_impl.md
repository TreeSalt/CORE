# MISSION: mantis_alpha_decay_monitor_impl
TYPE: IMPLEMENTATION
MISSION_ID: 02_RISK_E18_003_alpha_decay_monitor_impl

## DELIVERABLE
File: mantis_core/risk/alpha_decay_monitor.py

## INTERFACE CONTRACT
### Class: AlphaDecayMonitor
Methods: record_paper_result, record_live_result, compute_decay() -> DecayReport
### Dataclass: DecayReport (frozen)
