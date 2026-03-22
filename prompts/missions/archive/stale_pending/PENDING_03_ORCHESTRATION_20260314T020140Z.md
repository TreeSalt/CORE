# CLOUD TASK PACKAGE
# Model: claude-code | Tier: heavy | Domain: 03_ORCHESTRATION
# Security: INTERNAL | Cloud-eligible: True

DOMAIN: 03_ORCHESTRATION
SECURITY_CLASS: INTERNAL
MISSION: # MISSION: Session Checkpoint System
DOMAIN: 03_ORCHESTRATION
TASK: implement_session_checkpoints
TYPE: IMPLEMENTATION
VERSION: 1.0

## CONTEXT
The sovereign needs a fast way to see system status without reading
multiple JSON files. This creates a single-command health check.

## BLUEPRINT
Create scripts/session_status.py that prints:
1. Current engine version
2. Queue status (pending/ratified/failed counts)
3. Predatory Gate summary (survivors/killed)
4. Paper trading status (active windows, latest metrics)
5. Champion Registry top 3
6. Last 3 ERROR_LEDGER entries
7. Git status (dirty/clean, last commit)
8. Ollama status (running/stopped, loaded models)

Must run in <2 seconds. Human-readable terminal output with color codes.

## DELIVERABLE
File: scripts/session_status.py

## CONSTRAINTS
- Read-only access to all state files
- Must handle missing files gracefully (new install)
- No external API calls
- Output valid Python only
TASK: implement_session_checkpoints
CONSTRAINTS:
  - Proposals only. No direct execution.
  - No writes to 04_GOVERNANCE/
  - No hardcoded credentials
  - Fail closed on any constraint breach
  - Output valid Python code only


INSTRUCTIONS: Execute in Claude Code terminal. Return proposal to 08_IMPLEMENTATION_NOTES/.