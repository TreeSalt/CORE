# MISSION: Prefer-Heavy Tier Configuration
DOMAIN: 03_ORCHESTRATION
TYPE: IMPLEMENTATION

## DELIVERABLE
File: orchestration/tier_config.py

## REQUIREMENTS
- TierPreference enum: PREFER_HEAVY, PREFER_CRUISER, PREFER_SPRINTER, FORCE_HEAVY, FORCE_CRUISER
- get_effective_tier(preference, available_vram, available_ram, model_sizes) -> tuple of (tier, model, mode)
- When preference is PREFER_HEAVY: try heavy first, degrade gracefully to cruiser then sprinter
- When preference is FORCE_HEAVY: return ESCALATE if heavy cannot fit
- log_tier_decision(domain, desired, actual, reason) -> None
- Pure functions, no external calls
- Output valid Python only
