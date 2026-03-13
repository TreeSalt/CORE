# CLOUD TASK PACKAGE
# Model: claude-code | Tier: heavy | Domain: 03_ORCHESTRATION
# Security: INTERNAL | Cloud-eligible: True

DOMAIN: 03_ORCHESTRATION
SECURITY_CLASS: INTERNAL
MISSION: # MISSION: Alpha Synthesis Mission Generator
DOMAIN: 03_ORCHESTRATION
TASK: implement_alpha_synthesis_generator
TYPE: IMPLEMENTATION
VERSION: 1.0

## CONTEXT
Per ROADMAP v3.0, Epoch 3 uses LLM-guided gene-splicing. The 32B Heavy Lifter
reads the Champion Registry (winners) alongside the Graveyard (anti-patterns)
and synthesizes hybrid strategies combining winning traits.

## BLUEPRINT
Create a module that:
1. Reads state/champion_registry.json (or state/predatory_gate_survivors.json)
2. Reads docs/GRAVEYARD.md for anti-patterns
3. For each pair of surviving strategies, generates a MISSION file that:
   - Names the hybrid (e.g., "E3_001_gatekeeper_x_squeeze")
   - Describes which traits to combine from parent A and parent B
   - Explicitly lists anti-patterns from Graveyard as "DO NOT" constraints
   - Includes the correct prepare_data() interface spec
4. Writes missions to prompts/missions/ and adds them to MISSION_QUEUE.json
5. Maximum 5 hybrids per epoch (hardware budget constraint)

## DELIVERABLE
File: scripts/alpha_synthesis.py

## CONSTRAINTS
- Read-only access to Graveyard and Champion Registry
- Mission files go to prompts/missions/ (standard path)
- Queue entries follow existing schema exactly
- No external API calls
- Output valid Python only
TASK: implement_alpha_synthesis_generator
CONSTRAINTS:
  - Proposals only. No direct execution.
  - No writes to 04_GOVERNANCE/
  - No hardcoded credentials
  - Fail closed on any constraint breach
  - Output valid Python code only


INSTRUCTIONS: Execute in Claude Code terminal. Return proposal to 08_IMPLEMENTATION_NOTES/.