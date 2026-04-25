# MISSION: Mission Preflight Gate v2 — Brief Validator
DOMAIN: 03_ORCHESTRATION
TASK: 03_ORCH_E12_003_mission_preflight_v2
TYPE: IMPLEMENTATION
VERSION: 3.0

## EXACT IMPORTS:
```python
import re
import sys
import json
import yaml
from pathlib import Path
```

## CONTEXT
Mission briefs need validation before dispatch to prevent common failures:
missing deliverable paths, invalid domain names, missing import sections for
test missions, and invalid mission types.

## REQUIREMENTS
Write `scripts/mission_preflight.py` that accepts a brief path as a CLI argument
and validates:

1. A line starting with "DELIVERABLE" or "File:" exists in the brief
2. The DOMAIN line value matches a valid domain ID in 04_GOVERNANCE/DOMAINS.yaml
3. The TYPE line value is one of: IMPLEMENTATION, ARCHITECTURE, STRATEGIC_ARCHITECTURE, TEST
4. If TYPE is TEST, the brief must contain an "EXACT IMPORTS" section
5. If the domain is 00_PHYSICS_ENGINE or 02_RISK_MANAGEMENT, the brief must contain "EXACT IMPORTS"

Exit with code 0 if all checks pass. Exit with code 1 and print a JSON report
of failures if any check fails.

Usage: `python3 scripts/mission_preflight.py prompts/missions/some_brief.md`

## DELIVERABLE
File: scripts/mission_preflight.py

## CONSTRAINTS
- Pure regex and string matching — no LLM calls
- Output valid Python only
