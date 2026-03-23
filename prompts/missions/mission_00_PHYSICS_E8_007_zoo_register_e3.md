# MISSION: Register E8 Strategies in Champion Registry
DOMAIN: 00_PHYSICS_ENGINE
TYPE: IMPLEMENTATION

## DELIVERABLE
File: scripts/register_e8_strategies.py

## REQUIREMENTS
- Read E8 predatory gate results from reports/predatory/
- For each SURVIVOR, add entry to state/champion_registry.json
- Entry format: {strategy_id, epoch, topology, predatory_status, registered_at}
- For each GRAVEYARD casualty, append to docs/GRAVEYARD.md with reason
- No external API calls
- Output valid Python only
