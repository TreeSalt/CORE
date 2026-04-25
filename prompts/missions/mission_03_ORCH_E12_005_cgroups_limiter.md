# MISSION: Ollama cgroups v2 Resource Manager
DOMAIN: 03_ORCHESTRATION
TASK: 03_ORCH_E12_005_cgroups_limiter
TYPE: IMPLEMENTATION
VERSION: 3.0

## EXACT IMPORTS:
```python
import subprocess
import os
import logging
from pathlib import Path
```

## CONTEXT
Ollama can consume all available RAM when loading 27B models in SPLIT mode.
cgroups v2 lets us set hard memory limits to prevent OOM kills affecting
the rest of the system.

## REQUIREMENTS
Write `scripts/cgroup_manager.py` with these functions:

- `get_ollama_pid()`: Use subprocess to run `pgrep -f ollama` and return the PID
  as an integer, or None if Ollama is not running.
- `setup_cgroup(memory_max_gb, memory_high_gb)`: Create a systemd slice or write
  directly to cgroup v2 filesystem to set MemoryMax and MemoryHigh limits for
  the Ollama process. Return True on success, False on failure.
- `get_cgroup_stats()`: Read memory.current and memory.max from the cgroup
  filesystem. Return a dict with current_mb and max_mb.
- `is_ollama_in_cgroup()`: Check whether the Ollama PID is assigned to the cgroup.
- `teardown_cgroup()`: Remove the cgroup slice.

All functions should handle gracefully the case where cgroups v2 is not available.

## DELIVERABLE
File: scripts/cgroup_manager.py

## CONSTRAINTS
- Graceful failure without cgroups v2
- Never kill the Ollama process
- Output valid Python only
