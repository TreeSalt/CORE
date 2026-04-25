# MISSION: Test Suite — Infrastructure (Dual Lane + cgroups)
DOMAIN: 06_BENCHMARKING
TASK: 06_BENCH_E12_004_infra_test
TYPE: TEST
VERSION: 1.0

## CONTEXT
Tests for E12 infrastructure: dual-lane orchestrator and cgroup manager.

## EXACT IMPORTS:
```python
import sys
sys.path.insert(0, 'scripts')
from cgroup_manager import setup_cgroup, get_cgroup_stats, is_ollama_in_cgroup
```

## BLUEPRINT
TestCgroupManager: setup creates slice, stats readable, teardown removes,
graceful failure without cgroups v2 (4 tests)

TestDualLane: GPU lane processes sprinter, CPU lane processes cruiser,
heavy blocks both lanes, graceful shutdown, priority ordering (5 tests)

Mock subprocess calls — never actually create cgroups or invoke Ollama.

## DELIVERABLE
File: 06_BENCHMARKING/tests/03_ORCHESTRATION/test_infra_e12.py

## CONSTRAINTS
- pytest, unittest.mock
- NEVER create real cgroups in tests
- Output valid Python only
