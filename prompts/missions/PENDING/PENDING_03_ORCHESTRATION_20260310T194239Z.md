# CLOUD TASK PACKAGE
# Model: claude-code | Tier: heavy | Domain: 03_ORCHESTRATION
# Security: INTERNAL | Cloud-eligible: True

DOMAIN: 03_ORCHESTRATION
SECURITY_CLASS: INTERNAL
MISSION: MISSION: Wire Makefile Splinter Hook
DOMAIN: 03_ORCHESTRATION
TYPE: IMPLEMENTATION
VERSION: 1.0

CONTEXT — THE PROBLEM:
Every time make drop runs, it bumps the version (e.g. 9.9.26 → 9.9.27).
The forge then requires a file named:
  prompts/missions/TRADER_OPS_MASTER_IDE_REQUEST_v{NEW_VERSION}.txt
This file doesn't exist yet, so the forge FATAL-errors on every drop.
The human sovereign has been manually creating these files each time.
This must be automated.

WHAT ALREADY EXISTS:
- scripts/amend_prompt_version.py — takes --version arg, copies previous
  prompt file forward and appends a VERSION SPLINTER section
- Makefile variable: VERSION (auto-read from antigravity_harness/__init__.py)
- Makefile variable: VENV_PYTHON (.venv/bin/python3)
- The build target starts around line 161 in the Makefile

WHAT TO IMPLEMENT:
Patch the Makefile build target to call amend_prompt_version.py
BEFORE the forge checks for the prompt file.

The patch must insert these three lines at the START of the build target
recipe (before the existing TRADER_OPS_PROMPT_ID check):

	@echo "🧬 Splinter Agent: ensuring prompt file exists for v$(VERSION)..."
	@$(VENV_PYTHON) scripts/amend_prompt_version.py --version $(VERSION) 2>&1 | tail -5
	@git add prompts/missions/TRADER_OPS_MASTER_IDE_REQUEST_v$(VERSION).txt 2>/dev/null || true

CRITICAL CONSTRAINTS:
- Recipe lines MUST be indented with a TAB character, not spaces
- Do NOT modify any other part of the Makefile
- Do NOT change the amend_prompt_version.py script
- Output the exact 3-line patch with correct tab indentation
- Also output the sed command to insert it at the correct line

DELIVERABLE:
A Python script that:
1. Reads the Makefile
2. Finds the build target recipe start (line with TRADER_OPS_PROMPT_ID check)
3. Inserts the 3-line splinter hook immediately before it
4. Writes the patched Makefile back
5. Verifies the patch with a grep confirmation
TASK: wire_makefile_splinter_hook
CONSTRAINTS:
  - Proposals only. No direct execution.
  - No writes to 04_GOVERNANCE/
  - No hardcoded credentials
  - Fail closed on any constraint breach
  - Output valid Python code only


INSTRUCTIONS: Execute in Claude Code terminal. Return proposal to 08_IMPLEMENTATION_NOTES/.