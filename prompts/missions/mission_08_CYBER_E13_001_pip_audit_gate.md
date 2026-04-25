# MISSION: Dependency CVE Audit Gate
DOMAIN: 08_CYBERSECURITY
TASK: 08_CYBER_E13_001_pip_audit_gate
TYPE: IMPLEMENTATION
VERSION: 1.0

## CONTEXT
The repository's pre-commit hooks currently include detect-secrets but
have no dependency vulnerability scanning. Python dependencies in
requirements.txt are pinned with hashes but never audited against the
PyPI advisory database. This mission adds a pip-audit gate that runs
both as a pre-commit hook and as a standalone script invokable from
benchmark workflows.

The gate supports an allowlist for accepted risks (e.g., a CVE that
does not affect the project's specific use case). The allowlist is
itself version-controlled and auditable.

## EXACT IMPORTS:
```python
import os
import sys
import json
import logging
import subprocess
import argparse
from pathlib import Path
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import List, Dict, Optional, Set
```

## INTERFACE CONTRACT
The deliverable is `scripts/pip_audit_gate.py` containing both an
importable API and a CLI entry point.

### Constants
- DEFAULT_REQUIREMENTS = "requirements.txt"
- DEFAULT_ALLOWLIST = "08_CYBERSECURITY/.audit_allowlist.json"
- SEVERITY_ORDER = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]

### Dataclass: Vulnerability
Frozen dataclass with these fields:
```
vuln_id: str                # CVE or PYSEC identifier
package: str                # package name
installed_version: str
fix_versions: List[str]
severity: str               # LOW/MEDIUM/HIGH/CRITICAL/UNKNOWN
description: str
allowlisted: bool           # True if vuln_id is in allowlist
```

### Dataclass: AuditResult
Frozen dataclass with these fields:
```
generated_at: str           # ISO UTC
requirements_file: str
total_packages_scanned: int
vulnerabilities: List[Vulnerability]
critical_count: int
high_count: int
medium_count: int
low_count: int
allowlisted_count: int
gate_passed: bool
```

### Function: run_pip_audit(requirements_file: Path) -> List[Dict]
Invokes `pip-audit -r <requirements_file> --format json` via subprocess
with a 120-second timeout. Parses the JSON output and returns the raw
vulnerability dicts. Raises RuntimeError if pip-audit is not installed
or fails to execute.

### Function: load_allowlist(allowlist_path: Path) -> Set[str]
Loads the allowlist JSON file. The schema is:
```
{
  "allowlist": [
    {"vuln_id": "PYSEC-2024-XXX", "reason": "...", "added_at": "..."}
  ]
}
```
Returns a set of allowlisted vulnerability IDs. Returns empty set if the
file does not exist (no allowlist is the default).

### Function: parse_vulnerabilities(raw_vulns: List[Dict], allowlist: Set[str]) -> List[Vulnerability]
Converts raw pip-audit output into Vulnerability dataclasses. The
severity field is extracted from the raw data; if missing, defaults to
"UNKNOWN". The allowlisted field is True if the vuln_id is in the
allowlist set.

### Function: evaluate_gate(audit_result: AuditResult, fail_on_severity: str = "HIGH") -> bool
Returns True (gate passes) if no non-allowlisted vulnerability has
severity >= fail_on_severity. The severity comparison uses SEVERITY_ORDER.
For example, fail_on_severity="HIGH" means HIGH and CRITICAL vulnerabilities
fail the gate, but MEDIUM and LOW pass. Allowlisted vulnerabilities never
fail the gate regardless of severity.

### Function: run_audit(requirements_file: Path, allowlist_path: Path, fail_on_severity: str = "HIGH") -> AuditResult
The main orchestration function:
1. Calls run_pip_audit
2. Calls load_allowlist
3. Calls parse_vulnerabilities
4. Computes counts by severity
5. Calls evaluate_gate to set gate_passed
6. Returns populated AuditResult

### CLI Entry Point
When invoked with `python3 scripts/pip_audit_gate.py [--fail-on SEVERITY]`:
- Calls run_audit with default paths
- Prints AuditResult as JSON to stdout
- Exits 0 if gate_passed is True
- Exits 1 if gate_passed is False
- `--fail-on` defaults to "HIGH"
- `--requirements` overrides the default requirements file path
- `--allowlist` overrides the default allowlist path
- `--quiet` suppresses JSON output, prints only "PASS" or "FAIL"

## DELIVERABLE
File: scripts/pip_audit_gate.py

## BEHAVIORAL REQUIREMENTS
- pip-audit must be invoked via subprocess (not imported as a library)
- Subprocess timeout is mandatory (120 seconds)
- pip-audit unavailability is a CRITICAL failure (gate fails closed)
- Allowlist file format must be JSON with the documented schema
- All severity comparisons use SEVERITY_ORDER for consistency
- Allowlisted vulnerabilities are still reported but do not fail the gate
- Output JSON must be valid and parseable

## TEST REQUIREMENTS
The corresponding test mission will verify:
1. Vulnerability and AuditResult are valid frozen dataclasses
2. load_allowlist returns empty set when file does not exist
3. load_allowlist returns correct set when file exists
4. parse_vulnerabilities correctly marks allowlisted IDs
5. evaluate_gate passes when only LOW/MEDIUM vulns exist
6. evaluate_gate fails when CRITICAL vuln is not allowlisted
7. evaluate_gate passes when CRITICAL vuln IS allowlisted
8. CLI exits 0 on pass, 1 on fail
9. run_pip_audit raises RuntimeError when pip-audit binary missing

## CONSTRAINTS
- Pure stdlib (no pip-audit Python library import)
- Subprocess-based pip-audit invocation only
- Fail-closed on tool unavailability
- Output valid Python only
