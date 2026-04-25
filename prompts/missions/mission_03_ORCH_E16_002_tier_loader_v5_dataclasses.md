# MISSION: tier_loader_v5_dataclasses
TYPE: IMPLEMENTATION
MISSION_ID: 03_ORCH_E16_002_tier_loader_v5_dataclasses

## CONTEXT
The original tier_loader_v4 truncated mid-implementation due to context
window exhaustion. See E14_BACKLOG_001. This mission is the FIRST HALF
of a split: implement only the dataclasses.

## EXACT IMPORTS
```python
from dataclasses import dataclass, field
from typing import Optional
```

## INTERFACE CONTRACT
Deliverable: `mantis_core/orchestration/tier_loader_dataclasses.py`

### Dataclass: ModelInfo (frozen)
Fields:
- name (str)
- size_mb (int)
- context_window (int)
- supports_thinking (bool)

### Dataclass: TierMapping (frozen)
Fields:
- sprinter (ModelInfo)
- cruiser (ModelInfo)
- heavy (ModelInfo)

THIS IS A MODULE-LEVEL DEFINITION. Do NOT wrap these in a class.
Do NOT define them as methods. They are top-level @dataclass declarations.

## CONSTRAINTS
- Pure stdlib only
- File MUST be under 80 lines total
