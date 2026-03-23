# MISSION: Red Team Self-Test Runner
DOMAIN: 08_CYBERSECURITY
TYPE: IMPLEMENTATION

## DELIVERABLE
File: scripts/redteam/selftest_runner.py

## REQUIREMENTS
- Discover all probe modules in scripts/redteam/
- Execute each module's test suite
- Aggregate: total probes, passed, failed, severity breakdown
- JSON report: reports/security/SELFTEST_{timestamp}.json
- Markdown summary: reports/security/SELFTEST_{timestamp}.md
- Exit code 0 if no CRITICAL, 1 otherwise
- No external API calls
- Output valid Python only
