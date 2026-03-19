# Mission: 03_ORCH_E2_003_lockdown_status

## Domain
03_ORCHESTRATION

## Model Tier
Sprint (9b)

## Description
Integrate lockdown status into the core status dashboard.

REQUIREMENTS:
1. Read orchestration/LOCAL_LOCKDOWN.json
2. If lockdown enabled: show red lock icon with reason and timestamp
3. If lockdown disabled: show green unlock icon
4. Add between GIT status and MISSION QUEUE in the dashboard layout
5. Use ANSI colors consistent with existing dashboard style

ALLOWED IMPORTS: json, pathlib (already imported in core_cli.py)
OUTPUT: Updated cmd_status() in scripts/core_cli.py
TEST: Assert status output includes LOCKDOWN section.
