# MISSION: Implement queue reset-failed CLI Command
DOMAIN: 03_ORCHESTRATION
TASK: implement_queue_reset_failed
TYPE: IMPLEMENTATION

## CONTEXT
The CORE CLI advertises 'core queue reset-failed' in help text but it is not implemented. When a user runs 'core queue reset-failed', it should reset all missions with status ESCALATE or HARD_FAIL back to PENDING, log how many were reset, and update the queue file.

## DELIVERABLE
File: scripts/queue_reset_patch.py (to be integrated into core_cli.py cmd_queue function)

## REQUIREMENTS
- Read MISSION_QUEUE.json
- Find all missions where status is ESCALATE or HARD_FAIL
- Set their status to PENDING
- Add reset_reason and reset_at fields
- Write back to MISSION_QUEUE.json
- Print count of reset missions
- Also update core reconnect --reset to handle ESCALATE status
- No external API calls
- Output valid Python only
