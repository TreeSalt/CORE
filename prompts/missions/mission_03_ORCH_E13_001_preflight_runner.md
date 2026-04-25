# MISSION: Preflight Runner — Pre-Mission Health Gate
DOMAIN: 03_ORCHESTRATION
TASK: 03_ORCH_E13_001_preflight_runner
TYPE: IMPLEMENTATION
VERSION: 1.0

## CONTEXT
`mantis_core/orchestration/core_doctor.py` exists in the repository but is
never invoked anywhere in the orchestration pipeline. It is unemployed.
This mission builds a preflight runner that acts as a centralized health
gate before mission dispatch. The runner aggregates checks from multiple
sources, including the existing core_doctor module, and produces a single
structured verdict.

The preflight is designed to fail loud and fast: any critical condition
prevents mission dispatch. Warnings are logged but do not block.

## EXACT IMPORTS:
```python
import os
import sys
import json
import shutil
import subprocess
import logging
from pathlib import Path
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any
```

## INTERFACE CONTRACT
The deliverable is `scripts/preflight_runner.py` containing both an
importable API and a CLI entry point.

### Enum-equivalent constants
Define module-level string constants:
- SEVERITY_CRITICAL = "CRITICAL"
- SEVERITY_WARNING = "WARNING"
- SEVERITY_INFO = "INFO"

### Dataclass: HealthCheckResult
Frozen dataclass with these exact fields:
```
check_name: str
severity: str               # one of CRITICAL/WARNING/INFO
passed: bool
message: str
details: Dict[str, Any]
timestamp: str              # ISO format UTC
```

### Dataclass: PreflightVerdict
Frozen dataclass with these exact fields:
```
ok_to_dispatch: bool
critical_count: int
warning_count: int
info_count: int
checks: List[HealthCheckResult]
generated_at: str           # ISO format UTC
```

### Function: check_disk_space(min_free_gb: int = 5) -> HealthCheckResult
Verifies at least min_free_gb gigabytes are free in the repo's filesystem.
CRITICAL severity, fails if free space below threshold.

### Function: check_governor_seal() -> HealthCheckResult
Verifies `.governor_seal` exists and the AEC_HASH line is present and
matches the SHA256 of `04_GOVERNANCE/AGENTIC_ETHICAL_CONSTITUTION.md`.
CRITICAL severity, fails on any mismatch or missing file.

### Function: check_ollama_health() -> HealthCheckResult
Performs a GET request to `http://localhost:11434/api/tags` with a 5-second
timeout. Verifies the response is valid JSON and contains a non-empty
"models" list. CRITICAL severity. Use only stdlib (urllib.request) — no
requests library import.

### Function: check_vram_available(min_mb: int = 3000) -> HealthCheckResult
Invokes `nvidia-smi --query-gpu=memory.free --format=csv,nounits,noheader`
via subprocess. Parses the integer result. WARNING severity if below
min_mb. INFO severity if nvidia-smi is not installed (degraded but not
blocking).

### Function: check_doctor() -> HealthCheckResult
Attempts to import `mantis_core.orchestration.core_doctor`. If the import
succeeds, the function should call any callable module-level entry point
it can find (look for names like `run`, `main`, `diagnose`, or a class
named `Doctor`/`CoreDoctor` with a `run()` method). The result of the
doctor call is captured in the `details` field. Failure to import or
to find an entry point produces an INFO-severity result, not a failure.
This check is best-effort: doctor unavailability does not block dispatch.

### Function: run_preflight() -> PreflightVerdict
Calls all five check functions in sequence, aggregates results, computes
counts by severity, and returns a populated PreflightVerdict. The
ok_to_dispatch field is True only when critical_count == 0.

### CLI Entry Point
When invoked with `python3 scripts/preflight_runner.py`:
- Calls run_preflight()
- Prints the verdict as formatted JSON to stdout
- Exits with code 0 if ok_to_dispatch is True
- Exits with code 1 if ok_to_dispatch is False

When invoked with `python3 scripts/preflight_runner.py --quiet`:
- Same as above but suppresses JSON output, prints only "OK" or "FAIL"

## DELIVERABLE
File: scripts/preflight_runner.py

## BEHAVIORAL REQUIREMENTS
- All checks must complete within 30 seconds total
- No check is allowed to crash the runner — wrap each in try/except
- Doctor invocation must be best-effort with graceful degradation
- All timestamps must be timezone-aware UTC, ISO format
- Output must be valid JSON when not in quiet mode
- The script must be runnable standalone (no import-time side effects)

## TEST REQUIREMENTS
The corresponding test mission will verify:
1. HealthCheckResult and PreflightVerdict are valid frozen dataclasses
2. run_preflight returns a PreflightVerdict with all 5 checks executed
3. ok_to_dispatch is False if any CRITICAL check fails
4. ok_to_dispatch is True if only WARNING/INFO checks fail
5. CLI exits 0 when verdict is OK
6. CLI exits 1 when verdict is FAIL
7. check_doctor returns INFO (not failure) when core_doctor cannot be imported
8. JSON output is valid and parseable

## CONSTRAINTS
- Pure stdlib only (urllib.request, subprocess, dataclasses)
- No external HTTP libraries (no requests, no httpx)
- Must run on Python 3.10+
- Output valid Python only
