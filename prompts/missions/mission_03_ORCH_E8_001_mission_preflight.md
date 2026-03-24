# MISSION: Mission Preflight Gate
DOMAIN: 03_ORCHESTRATION
TYPE: IMPLEMENTATION

## DELIVERABLE
File: scripts/mission_preflight.py

## REQUIREMENTS
- check_mission(path) -> list of issues found
- Runs the same regex patterns the router uses against mission file content
- Reports which line number triggered which pattern
- Returns empty list if clean
- CLI usage: python3 scripts/mission_preflight.py path1.md path2.md
- Exit code 0 if all clean, 1 if any triggered
- No external calls
- Output valid Python only
