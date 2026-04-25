# MISSION: Self-Aware Model Tier Loader v4
DOMAIN: 03_ORCHESTRATION
TASK: 03_ORCH_E13_002_tier_loader_v4
TYPE: IMPLEMENTATION
VERSION: 4.0

## CONTEXT
The current tier mapping in DOMAINS.yaml hardcodes qwen3.5:27b as the
heavy tier. This dense 27B model has been crashing under VRAM pressure
on the GTX 1070 8GB, returning HTTP 500 errors during retries.

The Ollama instance has additional models available that were not in the
original tier configuration:
- qwen3-coder:30b (MoE architecture, ~3-4B active params, code-specialized)
- qwen3.5:35b (larger MoE, broader reasoning)

MoE architectures dramatically outperform dense models on consumer GPUs
because the active parameter footprint is smaller. This mission builds a
tier loader that queries Ollama at startup, identifies installed models,
and constructs an optimal tier mapping based on what is actually available.

The loader is read-only with respect to DOMAINS.yaml. It produces a
runtime tier mapping that supplements the static configuration.

## EXACT IMPORTS:
```python
import json
import logging
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from typing import Dict, List, Optional
```

## INTERFACE CONTRACT
The deliverable is `mantis_core/orchestration/tier_loader.py` containing:

### Dataclass: ModelInfo
Frozen dataclass with these fields:
```
name: str                   # full model name (e.g., "qwen3-coder:30b")
parameter_size: str         # e.g., "30.5B"
parameter_count_b: float    # parsed numeric, e.g., 30.5
family: str                 # e.g., "qwen3moe"
is_moe: bool                # True if family contains "moe"
quantization: str           # e.g., "Q4_K_M"
size_bytes: int             # disk size
```

### Dataclass: TierMapping
Frozen dataclass with these fields:
```
sprinter: Optional[str]     # 4B-class model name, fast small tasks
cruiser: Optional[str]      # 9-13B-class model name, standard work
heavy: Optional[str]        # 27-32B model, prefers MoE for stability
architect: Optional[str]    # 30B+ MoE for ARCHITECTURE missions
fallback: Optional[str]     # any available model as last resort
loaded_at: str              # ISO timestamp
```

### Function: query_ollama_models() -> List[ModelInfo]
Performs a GET to `http://localhost:11434/api/tags` with 10-second timeout.
Parses the JSON response and constructs ModelInfo objects for each model.
The is_moe field is True when the family field contains "moe" (case
insensitive). The parameter_count_b is parsed by stripping "B" from
parameter_size and converting to float (e.g., "30.5B" -> 30.5).
Raises RuntimeError on connection failure or invalid response.

### Function: select_sprinter(models: List[ModelInfo]) -> Optional[str]
Returns the smallest qwen-family model with parameter_count_b <= 5.0.
Prefers higher quantization quality (Q4_K_M > Q4_0). Returns None if
no suitable model exists.

### Function: select_cruiser(models: List[ModelInfo]) -> Optional[str]
Returns the smallest qwen-family model with 5.0 < parameter_count_b <= 14.0.
Prefers Q4_K_M quantization. Returns None if no suitable model exists.

### Function: select_heavy(models: List[ModelInfo]) -> Optional[str]
Returns a model with 25.0 <= parameter_count_b <= 32.0, **strongly
preferring MoE architectures over dense ones for stability**. If both
MoE and dense candidates exist in the size range, the MoE wins. Among
MoE candidates of similar size, prefer code-specialized models (name
contains "coder"). Returns None if no suitable model exists.

### Function: select_architect(models: List[ModelInfo]) -> Optional[str]
Returns the largest available MoE model with parameter_count_b >= 30.0.
Prefers non-coder MoE for broader reasoning. Returns None if no suitable
MoE exists, in which case the architect tier falls back to whatever heavy
tier was selected.

### Function: load_tier_mapping() -> TierMapping
Calls query_ollama_models, then runs all four selectors, and constructs a
TierMapping with the results. Sets fallback to the largest available model.
loaded_at is the current UTC timestamp in ISO format. If query_ollama_models
raises, returns a TierMapping with all None fields and a stub fallback.

### Function: get_model_for_tier(tier: str) -> Optional[str]
Convenience accessor: returns the model name for a given tier string.
Valid tier values: "sprinter", "cruiser", "heavy", "architect", "fallback".
Calls load_tier_mapping internally (no caching at this layer — caching is
the caller's responsibility).

### Function: describe_mapping(mapping: TierMapping) -> str
Returns a human-readable multi-line description suitable for logging:
```
Tier Mapping (loaded at <timestamp>):
  sprinter:  qwen3.5:4b
  cruiser:   qwen3.5:9b
  heavy:     qwen3-coder:30b (MoE)
  architect: qwen3.5:35b (MoE)
  fallback:  qwen3.5:27b
```
Annotates MoE models with "(MoE)" suffix.

## DELIVERABLE
File: mantis_core/orchestration/tier_loader.py

## BEHAVIORAL REQUIREMENTS
- Pure stdlib networking (urllib only, no requests)
- Read-only — never modifies DOMAINS.yaml or any configuration file
- Deterministic given the same Ollama state
- Graceful degradation when Ollama is unavailable
- All timestamps timezone-aware UTC, ISO format
- Logging via the standard logging module, never print()
- MoE preference is strict: a 27B MoE always beats a 27B dense for heavy tier

## TEST REQUIREMENTS
The corresponding test mission will verify:
1. ModelInfo and TierMapping are valid frozen dataclasses
2. query_ollama_models raises RuntimeError on connection failure
3. select_heavy prefers MoE over dense in the same size range
4. select_architect returns None gracefully when no MoE >=30B available
5. load_tier_mapping returns a valid TierMapping even when Ollama fails
6. get_model_for_tier returns None for invalid tier names
7. describe_mapping output includes (MoE) annotation for MoE models

## CONSTRAINTS
- Pure stdlib (urllib.request, dataclasses, typing)
- No external HTTP libraries
- No file I/O — read-only network operations
- No global mutable state
- Output valid Python only
