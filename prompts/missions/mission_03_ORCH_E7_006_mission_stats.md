# MISSION: Mission Statistics CLI Command
DOMAIN: 03_ORCHESTRATION
TYPE: IMPLEMENTATION

## DELIVERABLE
File: scripts/mission_stats.py

## REQUIREMENTS
- Read all historical MISSION_QUEUE.json entries and proposals
- Calculate: total missions ever, pass rate by epoch, avg time per mission
- Calculate: missions by domain, most productive domain
- Display as formatted table in terminal
- Callable as: python3 scripts/mission_stats.py
- No external API calls
- Output valid Python only
