# MISSION: mantis_dashboard_data_endpoint
TYPE: IMPLEMENTATION
MISSION_ID: 00_PHYSICS_E18_005_dashboard_data_endpoint

## DELIVERABLE
File: mantis_core/dashboard/state_writer.py

## INTERFACE CONTRACT
### Function: write_dashboard_state(pipeline_state, output_path) -> None
Atomically writes the dashboard JSON state file. Called from MantisLivePipeline.
