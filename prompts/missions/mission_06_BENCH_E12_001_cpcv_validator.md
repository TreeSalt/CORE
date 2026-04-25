# MISSION: CPCV — Combinatorial Purged Cross-Validation
DOMAIN: 06_BENCHMARKING
TASK: 06_BENCH_E12_001_cpcv_validator
TYPE: IMPLEMENTATION
VERSION: 1.0

## CONTEXT
Standard walk-forward optimization overfits. CPCV generates all possible
train/test combinations with purging to prevent lookahead bias.

## EXACT IMPORTS:
```python
import numpy as np
from itertools import combinations
from dataclasses import dataclass
from typing import Callable, Optional
import json
from pathlib import Path
```

## BLUEPRINT
Create `06_BENCHMARKING/cpcv_validator.py`:

1. `class CPCVValidator`:
   - `__init__(n_groups, n_test_groups, purge_window)`: configure split params
   - `generate_splits(data_length)`: yield (train_indices, test_indices) for all combos
   - `purge(train_idx, test_idx, purge_window)`: remove train samples near test boundary
   - `validate_strategy(strategy_fn, data, metric_fn)`: run strategy across all splits
   - `get_results()`: return dict with mean_metric, std_metric, n_splits, worst_split
   - `is_overfit(threshold)`: True if std > threshold * mean (high variance = overfit)

2. Purge logic: remove any training sample within `purge_window` bars of any test sample

## DELIVERABLE
File: 06_BENCHMARKING/cpcv_validator.py

## CONSTRAINTS
- numpy for array operations
- No lookahead bias (purging is mandatory)
- Output valid Python only
