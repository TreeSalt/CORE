# CLOUD TASK PACKAGE
# Model: claude-code | Tier: heavy | Domain: 03_ORCHESTRATION
# Security: INTERNAL | Cloud-eligible: True

DOMAIN: 03_ORCHESTRATION
SECURITY_CLASS: INTERNAL
MISSION: # MISSION: Auto-Deploy Pipeline — Proposal to Target Path
DOMAIN: 03_ORCHESTRATION
TASK: implement_auto_deploy
TYPE: IMPLEMENTATION
VERSION: 1.0

## CONTEXT
Current gap: the factory writes proposals to 08_IMPLEMENTATION_NOTES/ as markdown
containing Python code. After ratification, nothing extracts the code to its
declared DELIVERABLE path. Deployment is manual (sed extraction). This must be
automated.

## BLUEPRINT
Create an auto-deploy script that:
1. Scans 08_IMPLEMENTATION_NOTES/ for RATIFIED proposals
2. For each, reads the DELIVERABLE path from the proposal header
3. Extracts the Python code block (```python ... ```)
4. Writes it to the DELIVERABLE path
5. Validates the extracted code: syntax check (ast.parse), import check
6. Logs deployment to state/deployment_log.json
7. If DELIVERABLE path is in 04_GOVERNANCE/ → REFUSE (constitutional violation)
8. If code fails syntax check → REFUSE and log error

## DELIVERABLE
File: scripts/deploy_ratified.py

## CONSTRAINTS
- NEVER write to 04_GOVERNANCE/
- Must verify RATIFIED status before deploying
- Must ast.parse() before writing
- Idempotent — running twice produces same result
- Output valid Python only
TASK: implement_auto_deploy
CONSTRAINTS:
  - Proposals only. No direct execution.
  - No writes to 04_GOVERNANCE/
  - No hardcoded credentials
  - Fail closed on any constraint breach
  - Output valid Python code only


INSTRUCTIONS: Execute in Claude Code terminal. Return proposal to 08_IMPLEMENTATION_NOTES/.