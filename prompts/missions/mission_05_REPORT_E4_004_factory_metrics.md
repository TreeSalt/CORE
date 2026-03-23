# MISSION: Factory Metrics Exporter
DOMAIN: 05_REPORTING
TYPE: IMPLEMENTATION

## DELIVERABLE
File: 05_REPORTING/reporting_domain/factory_metrics.py

## REQUIREMENTS
- Read all RATIFICATION and ESCALATION files from 08_IMPLEMENTATION_NOTES/
- Calculate: missions per epoch, avg time per mission, pass rate trend
- Calculate: missions per domain, busiest domain, most escalated domain
- Output JSON: reports/metrics/FACTORY_METRICS_{timestamp}.json
- Output Markdown summary alongside
- No external API calls
- Output valid Python only
