# MISSION: Dashboard Data API — Factory State Exporter
DOMAIN: 05_REPORTING
TASK: implement_dashboard_data_api
TYPE: IMPLEMENTATION
VERSION: 1.0

## CONTEXT
Per ROADMAP v3.0, the Tamagotchi dashboard needs a data layer.
This module exports real-time factory state as structured JSON
that any frontend (web, E-Ink, voxel world) can consume.

## BLUEPRINT
Create a FactoryStateExporter class that reads:
1. orchestration/MISSION_QUEUE.json → mission status summary
2. orchestration/ORCHESTRATOR_STATE.json → run history
3. orchestration/VRAM_STATE.json → hardware utilization
4. state/champion_registry.json → strategy performance
5. state/predatory_gate_survivors.json → survivor list
6. state/paper_trading_matrix.json → active trading windows
7. docs/GRAVEYARD.md → failure count and latest entries

And produces a single dashboard_state.json containing:
- factory_status: IDLE / RUNNING / WAITING_RATIFICATION
- active_missions: count and names
- hardware: vram_used_pct, ram_used_pct, model_loaded
- strategies: total, active, dormant, killed
- paper_trading: per-window status and latest metrics
- graveyard_size: total entries
- version: current engine version
- uptime: time since last orchestrator start

## DELIVERABLE
File: 05_REPORTING/reporting_domain/factory_state_exporter.py

## CONSTRAINTS
- Read-only access to all state files
- Output must be valid JSON
- No external API calls
- Output valid Python only
