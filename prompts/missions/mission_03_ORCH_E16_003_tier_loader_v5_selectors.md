# MISSION: tier_loader_v5_selectors
TYPE: IMPLEMENTATION
MISSION_ID: 03_ORCH_E16_003_tier_loader_v5_selectors

## CONTEXT
Second half of the tier_loader_v5 split. Imports the dataclasses from
the first half (tier_loader_dataclasses.py). Implements the selector
functions as MODULE-LEVEL FUNCTIONS, not methods.

## EXACT IMPORTS
```python
import json
import subprocess
import requests
from pathlib import Path
from typing import Optional
from mantis_core.orchestration.tier_loader_dataclasses import ModelInfo, TierMapping
```

## INTERFACE CONTRACT
Deliverable: `mantis_core/orchestration/tier_loader.py`

### Function: query_ollama_models() -> list[ModelInfo]
GET http://localhost:11434/api/tags. Parse response into list of
ModelInfo. Use stdlib urllib.request, not requests library.

### Function: query_available_vram_mb() -> int
Run `nvidia-smi --query-gpu=memory.free --format=csv,nounits,noheader`
and parse the integer.

### Function: select_sprinter(models: list[ModelInfo], vram_mb: int) -> ModelInfo
Return the smallest model that fits in VRAM with margin.

### Function: select_cruiser(models: list[ModelInfo], vram_mb: int) -> ModelInfo
Return mid-size model that fits.

### Function: select_heavy(models: list[ModelInfo], vram_mb: int) -> ModelInfo
Return largest model that fits, even if RAM-spillover required.

### Function: load_tier_mapping() -> TierMapping
Compose query_ollama_models + query_available_vram_mb + select_* into
a complete TierMapping.

## CRITICAL
- These are MODULE-LEVEL FUNCTIONS, not methods of a class
- Do NOT wrap them in a class definition
- Do NOT name a class anything containing the word "Mapping"

## CONSTRAINTS
- stdlib + requests
