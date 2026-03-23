# MISSION: Security Dashboard Data Aggregator
DOMAIN: 08_CYBERSECURITY
TYPE: IMPLEMENTATION

## DELIVERABLE
File: scripts/redteam/security_dashboard.py

## REQUIREMENTS
- Read all reports from reports/security/
- Aggregate: total scans, findings by severity, trend over time
- Read credential scan results, governance bypass results, supply chain results
- Output consolidated JSON: reports/security/DASHBOARD_{timestamp}.json
- Include: last_scan_time, total_findings, critical_count, open_issues
- No external API calls
- Output valid Python only
