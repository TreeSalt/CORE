# MISSION: mantis_results_reporter
TYPE: IMPLEMENTATION
MISSION_ID: 05_REPORT_E18_001_results_reporter

## DELIVERABLE
File: mantis_core/reporting/results_reporter.py

## INTERFACE CONTRACT
### Function: generate_report(run_results: dict, output_path: Path) -> None
Generates a markdown report with: trade summary, P&L curve (text-art),
regime breakdown, alpha decay analysis.
