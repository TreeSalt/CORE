# MISSION: Domain Health Report
DOMAIN: 05_REPORTING
TYPE: IMPLEMENTATION

## DELIVERABLE
File: 05_REPORTING/reporting_domain/domain_health.py

## REQUIREMENTS
- For each of the 9 domains: count files, count tests, count proposals, count escalations
- Calculate health score per domain (0-100) based on test coverage and pass rate
- Identify domains with zero tests as CRITICAL
- Output Markdown table: domain, files, tests, proposals, escalations, health_score
- Output to reports/health/DOMAIN_HEALTH_{timestamp}.md
- No external API calls
- Output valid Python only
