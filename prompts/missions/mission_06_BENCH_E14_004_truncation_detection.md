# MISSION: TRUNCATION_DETECTION_GATE
DOMAIN: 06_BENCHMARKING
TYPE: IMPLEMENTATION
MISSION_ID: 06_BENCH_E14_004_truncation_detection

## CONTEXT
tier_loader_v4 ended at line 332 with `def select_sprinter(self) -> List[ModelInfo]:`
and no body. Context window exhausted mid-method. See E14_BACKLOG_001.

## EXACT IMPORTS
```python
import ast
import re
from pathlib import Path
```

## INTERFACE CONTRACT
Deliverable: `06_BENCHMARKING/gates/truncation_detection.py`

### Function: detect_truncation(code: str) -> tuple[bool, str]
Returns (is_truncated, reason). Truncation indicators:
1. Last non-blank line ends with `:` (signature without body)
2. ast.parse fails with "expected indented block"
3. Final indent level > 0 with no closing dedent
4. File ends inside unbalanced string literal
5. File ends with `pass  # TODO` or `pass  # placeholder`

### Function: gate_truncation_detection(proposal_path: Path) -> tuple[bool, str]
Extract largest code block, run detect_truncation, return result.

## CONSTRAINTS
- Pure stdlib (ast, re)
- Cheap to run (this is the first gate, runs on every proposal)
