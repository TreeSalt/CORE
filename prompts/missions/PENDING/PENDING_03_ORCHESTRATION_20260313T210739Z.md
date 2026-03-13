# CLOUD TASK PACKAGE
# Model: claude-code | Tier: heavy | Domain: 03_ORCHESTRATION
# Security: INTERNAL | Cloud-eligible: True

DOMAIN: 03_ORCHESTRATION
SECURITY_CLASS: INTERNAL
MISSION: # MISSION: Fix COUNCIL_CANON.yaml Duplicate Pubkey Bug
DOMAIN: 03_ORCHESTRATION
TASK: fix_council_canon_dedup
TYPE: IMPLEMENTATION
VERSION: 1.0

## CONTEXT
The forge's _sync_council_canon() function in antigravity_harness/forge/build.py
appends sovereign_pubkey_sha256 on every build instead of replacing the existing
line. This causes the YAML file to accumulate duplicate entries.

## BLUEPRINT
Fix the _sync_council_canon() function:
1. Find the re.sub() call that writes sovereign_pubkey_sha256
2. Change it from appending to replacing — if the key already exists, update it
3. After the fix, the YAML should have exactly ONE sovereign_pubkey_sha256 line
4. Add a post-write validation: read back the file, count occurrences, assert == 1

## DELIVERABLE
A patch description for antigravity_harness/forge/build.py

## CONSTRAINTS
- ONLY modify the _sync_council_canon() function
- Do NOT change any other function in build.py
- The fix must be idempotent (running forge multiple times produces same result)
- Output valid Python only
TASK: fix_council_canon_dedup
CONSTRAINTS:
  - Proposals only. No direct execution.
  - No writes to 04_GOVERNANCE/
  - No hardcoded credentials
  - Fail closed on any constraint breach
  - Output valid Python code only


INSTRUCTIONS: Execute in Claude Code terminal. Return proposal to 08_IMPLEMENTATION_NOTES/.