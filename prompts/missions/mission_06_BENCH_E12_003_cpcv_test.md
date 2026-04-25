# MISSION: Test Suite — CPCV Validator
DOMAIN: 06_BENCHMARKING
TASK: 06_BENCH_E12_003_cpcv_test
TYPE: TEST
VERSION: 1.0

## CONTEXT
Tests for the Combinatorial Purged Cross-Validation system.

## EXACT IMPORTS:
```python
import sys
sys.path.insert(0, '06_BENCHMARKING')
from cpcv_validator import CPCVValidator
import numpy as np
```

## BLUEPRINT
TestCPCVValidator: splits generated correctly, purge removes boundary samples,
no train/test overlap, all data covered, n_splits matches combinatorial formula (5 tests)

TestOverfitDetection: consistent strategy passes, random strategy flagged,
high variance flagged, low sample count warns (4 tests)

## DELIVERABLE
File: 06_BENCHMARKING/tests/06_BENCHMARKING/test_cpcv_validator.py

## CONSTRAINTS
- pytest, numpy
- Output valid Python only
