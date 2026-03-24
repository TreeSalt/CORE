# MISSION: Epoch Dashboard Generator
DOMAIN: 05_REPORTING
TYPE: IMPLEMENTATION

## DELIVERABLE
File: scripts/epoch_dashboard.py

## REQUIREMENTS
- read_run_loop_state(path) -> list of run records
- compute_metrics(runs) -> dict: total, passed, failed, pass_rate, avg_attempts, domain_breakdown
- generate_markdown(metrics, output_path) -> None
- generate_json(metrics, output_path) -> None
- All paths are function parameters
- No external calls
- Output valid Python only
