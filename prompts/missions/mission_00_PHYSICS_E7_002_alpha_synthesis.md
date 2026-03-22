# MISSION: Alpha Synthesis Generator
DOMAIN: 00_PHYSICS_ENGINE
TASK: implement_alpha_synthesis
TYPE: IMPLEMENTATION

## CONTEXT
Per ROADMAP v3.0: read the Champion Registry (survivors) and Graveyard (anti-patterns). For each pair of survivors, generate a hybrid mission file that combines winning traits while listing anti-patterns as explicit constraints. Maximum 5 hybrids per epoch.

## DELIVERABLE
File: scripts/alpha_synthesis.py

## REQUIREMENTS
- Read state/champion_registry.json for survivors
- Read docs/GRAVEYARD.md for anti-patterns
- Generate mission files for up to 5 hybrid strategies
- Each mission names the hybrid, describes parent traits, lists anti-patterns as DO NOT constraints
- Write missions to prompts/missions/ and entries to MISSION_QUEUE.json
- No external API calls
- Output valid Python only
