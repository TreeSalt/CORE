# CLOUD TASK PACKAGE
# Model: claude-code | Tier: heavy | Domain: 07_INTEGRATION
# Security: INTERNAL | Cloud-eligible: True

DOMAIN: 07_INTEGRATION
SECURITY_CLASS: INTERNAL
MISSION: # MISSION: Repo Polish — .gitignore + Directory Cleanup
DOMAIN: 07_INTEGRATION
TASK: implement_repo_polish
TYPE: IMPLEMENTATION
VERSION: 1.0

## BLUEPRINT
Create a script that:
1. Updates .gitignore to exclude noise from GitHub view:
   - state/*.py (temp gate runner files)
   - orchestration/last_drop.log
   - dist/ (build artifacts — too large for GitHub)
2. Creates a clean docs/ARCHITECTURE.md with:
   - One-paragraph project description
   - Directory tree (top 2 levels only) with one-line descriptions
   - Link to README.md for full details
3. Ensures every domain directory (00-08) has an __init__.py
4. Ensures every domain directory has a one-line README.md

## DELIVERABLE
File: scripts/polish_repo.py

## CONSTRAINTS
- Must NOT delete any files (only add .gitignore entries and docs)
- Must NOT modify 04_GOVERNANCE/
- Output valid Python only
TASK: implement_repo_polish
CONSTRAINTS:
  - Proposals only. No direct execution.
  - No writes to 04_GOVERNANCE/
  - No hardcoded credentials
  - Fail closed on any constraint breach
  - Output valid Python code only


INSTRUCTIONS: Execute in Claude Code terminal. Return proposal to 08_IMPLEMENTATION_NOTES/.