# MISSION: Epoch Dashboard — Factory State Exporter
DOMAIN: 05_REPORTING
TASK: 05_REPORT_E11_001_epoch_dashboard
TYPE: IMPLEMENTATION
VERSION: 1.0

## CONTEXT
The factory produces state across multiple files. There is no single unified view.
For demos, README badges, and dashboards, we need one function that exports the
complete factory state as structured JSON.

## BLUEPRINT
Create a factory state exporter:

1. Read MISSION_QUEUE.json: total missions by status, pass rates, epoch info
2. Read benchmark reports: average score, common failure gate, median gen time
3. Read escalations: count, oldest unresolved age
4. Hardware snapshot: VRAM, loaded models, uptime
5. Output a JSON blob with generated_at timestamp and one-line summary
6. Also generate compact Markdown summary for README/LinkedIn

## DELIVERABLE
File: mantis_core/reporting/epoch_dashboard.py

## CONSTRAINTS
- Python standard library + subprocess for hardware checks
- Handle missing files gracefully (new install has no reports)
- Read-only — never modifies state
- Output valid Python only
