# MISSION: Intent Compiler v1
DOMAIN: 03_ORCHESTRATION
TASK: implement_intent_compiler_v1
TYPE: IMPLEMENTATION

## CONTEXT
Per ROADMAP v3.0 Phase 2B: Build the Intent Compiler that translates imprecise human input into fully-specified mission queue entries. It reads DOMAINS.yaml, CHECKPOINTS.yaml, Champion Registry, Graveyard, and OPERATOR_INSTANCE.yaml to generate missions.

## DELIVERABLE
File: scripts/intent_compiler.py

## REQUIREMENTS
- Accept a natural language string as input (e.g. "build me a momentum strategy")
- Read DOMAINS.yaml to determine correct domain
- Read docs/GRAVEYARD.md to extract anti-pattern constraints
- Read state/champion_registry.json for existing strategy context
- Read OPERATOR_INSTANCE.yaml for hardware and risk constraints
- Generate a complete mission file with domain, task, type, constraints, deliverable
- Write to prompts/missions/ and optionally add to MISSION_QUEUE.json
- No external API calls (uses local LLM via Ollama for NL parsing)
- Output valid Python only
