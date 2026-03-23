# MISSION: Session Summary Generator v2
DOMAIN: 05_REPORTING
TYPE: IMPLEMENTATION

## DELIVERABLE
File: scripts/session_summary_v2.py

## REQUIREMENTS
- Read ORCHESTRATOR_STATE.json and MISSION_QUEUE.json
- Calculate: total missions, pass rate, domains covered, runtime
- Read git log for session commits
- Markdown summary for public sharing
- Output to reports/sessions/SESSION_{timestamp}.md
- No external API calls
- Output valid Python only
