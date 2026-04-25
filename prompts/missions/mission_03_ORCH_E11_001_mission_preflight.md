# MISSION: Mission Preflight Gate
DOMAIN: 03_ORCHESTRATION
TASK: 03_ORCH_E11_001_mission_preflight
TYPE: IMPLEMENTATION
VERSION: 1.0

## CONTEXT
The factory currently sends mission briefs directly to models without pre-validation.
This causes preventable failures: briefs containing patterns that trigger the secrets
scanner (false positives on trigger words), briefs with missing required fields, and
briefs referencing nonexistent deliverable paths. Post-hoc benchmarking catches these
after wasting a full generation cycle. A deterministic preflight gate catches them
before the model is ever invoked.

Principle: "Algorithms for the deterministic, LLMs for the creative."

## BLUEPRINT
Create a preflight validator that runs BEFORE model invocation:

1. Parse the mission brief markdown and extract required fields:
   - DOMAIN, TASK, TYPE, DELIVERABLE path
   - Fail if any required field is missing

2. Validate the DELIVERABLE path:
   - Parent directory must exist
   - Path must NOT be inside 04_GOVERNANCE/ (fiduciary air gap)
   - Path must end in .py, .md, .yaml, or .json

3. Run detect-secrets scan on the mission brief text itself:
   - If the brief contains patterns that would trigger credential scanning,
     flag them BEFORE the model generates code containing the same patterns
   - Return a list of flagged patterns with line numbers

4. Validate mission brief is not empty and contains at least a CONTEXT and
   BLUEPRINT section

5. Return a PreflightResult dataclass:
   - passed: bool
   - errors: list[str]
   - warnings: list[str]
   - brief_hash: str (SHA-256 of brief content for audit trail)

## DELIVERABLE
File: mantis_core/orchestration/mission_preflight.py

## EXPECTED OUTPUT EXAMPLE
```python
from dataclasses import dataclass, field

@dataclass
class PreflightResult:
    passed: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    brief_hash: str = ""

def run_preflight(mission_brief_path: str) -> PreflightResult:
    ...
```

## CONSTRAINTS
- Pure Python standard library only (pathlib, hashlib, re, dataclasses)
- No external API calls
- No file writes — read-only validation
- Must be importable and callable from orchestrator_loop.py
- Output valid Python only
