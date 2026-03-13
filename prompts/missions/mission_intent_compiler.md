# MISSION: Intent Compiler — Natural Language to Mission
DOMAIN: 03_ORCHESTRATION
TASK: implement_intent_compiler
TYPE: ARCHITECTURE
VERSION: 1.0

## CONTEXT
Per ROADMAP v3.0, the Intent Compiler bridges imprecise human input to
fully-specified factory missions. This is an ARCHITECTURE proposal — design
the interface and data flow, not the full implementation (that requires
cloud LLM access for natural language understanding).

## BLUEPRINT
Design the Intent Compiler architecture:
1. Input interface: accepts natural language string + operator context
2. Context gathering: reads DOMAINS.yaml, CHECKPOINTS.yaml, Champion Registry,
   Graveyard, Hardware state, OPERATOR_INSTANCE.yaml
3. Output: a fully-specified MISSION_QUEUE entry with all required fields
4. Validation: runs Prompt Quality Validator on generated mission before queue
5. Escalation: if confidence < threshold, asks human for clarification

Document the data flow as a class skeleton with method signatures,
docstrings, and type hints. Include example input/output pairs.

## DELIVERABLE
File: 03_ORCHESTRATION/orchestration_domain/intent_compiler.py

## CONSTRAINTS
- ARCHITECTURE proposal — class skeleton + docstrings, not full implementation
- Must reference all existing governance files by path
- Must include the Prompt Quality Validator as a pre-queue gate
- No external API calls in the skeleton
- Output valid Python only
