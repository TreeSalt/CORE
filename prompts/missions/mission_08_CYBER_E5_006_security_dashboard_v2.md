# MISSION: Security Dashboard Aggregator
DOMAIN: 08_CYBERSECURITY
TYPE: IMPLEMENTATION

## DELIVERABLE
File: scripts/redteam/security_dashboard.py

## REQUIREMENTS
- read_reports(reports_dir: str) -> list: scan directory for JSON report files
- aggregate(reports: list) -> dict: total scans, findings by severity, trend data
- generate_json(aggregated: dict, output_path: str) -> None: write consolidated JSON
- generate_markdown(aggregated: dict, output_path: str) -> None: write summary markdown
- All file paths are function parameters — no hardcoded paths
- No external calls of any kind
- Output valid Python only
