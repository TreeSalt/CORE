# Mission: Cruiser Tier — Three-Tier Model Routing

## Domain
03_ORCHESTRATION

## Model Tier
Sprint (9b)

## Description
Update the semantic router to support three model tiers instead of two.

CURRENT STATE: select_tier() in orchestration/semantic_router.py supports sprinter and heavy.
NEW STATE: Add cruiser tier between sprinter and heavy.

TIER DEFINITIONS (hardware-relative):
- sprinter: sub-9B models, fits entirely in VRAM, pure GPU
- cruiser: 9B-24B models, GPU-accelerated with minimal CPU spill  
- heavy: 24B+ models, deep reasoning, expects CPU overflow

REQUIREMENTS:
1. Add "cruiser" as valid tier in select_tier()
2. Read cruiser_model from domain config (DOMAINS.yaml)
3. Routing logic: primary_tier from config is default, escalation_trigger can override
4. Token escalation: sprinter -> cruiser -> heavy based on token count
5. Log which tier was selected and why

The function signature stays the same: select_tier(domain, mission_text) -> tuple[str, str]
Domain configs will need a new field: cruiser_model

ALLOWED IMPORTS: Only modify existing imports in semantic_router.py
OUTPUT: Updated select_tier() function in orchestration/semantic_router.py
TEST: Assert select_tier returns cruiser when primary_tier is cruiser. Assert token escalation from sprinter goes to cruiser before heavy.
