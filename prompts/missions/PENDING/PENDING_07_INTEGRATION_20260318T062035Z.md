# CLOUD TASK PACKAGE
# Model: claude-code | Tier: heavy | Domain: 07_INTEGRATION
# Security: INTERNAL | Cloud-eligible: True

DOMAIN: 07_INTEGRATION
SECURITY_CLASS: INTERNAL
MISSION: # Mission: core-sdk constitution.py — Constitutional Schema Loader

## Domain
07_INTEGRATION

## Model Tier
Heavy (27b)

## Description
Create core_sdk/constitution.py that loads and validates constitutional governance configs.

EXACT FUNCTIONS:

1. load_domains(path: Path) -> dict — load DOMAINS.yaml, return parsed dict
2. validate_domain(domain_id: str, domains: dict) -> bool — check domain exists and has required fields
3. get_security_classification(domain_id: str, domains: dict) -> str — return security level for domain
4. get_model_tier(domain_id: str, domains: dict) -> str — return model tier for domain
5. is_human_only(domain_id: str, domains: dict) -> bool — check if domain requires human-only access

ALL imports from Python stdlib ONLY (pathlib, typing, json, yaml is NOT stdlib).
Since yaml is not stdlib, parse YAML manually or use json. If the config is YAML, provide a simple YAML subset parser that handles the flat key-value structure of DOMAINS.yaml.
NO external dependencies.

OUTPUT: core_sdk/constitution.py
TEST: Create a mock domains dict. Assert validate_domain returns True for known domain. Assert is_human_only returns True for 04_GOVERNANCE.
TASK: 07_SDK_E1_004_constitution
CONSTRAINTS:
  - Proposals only. No direct execution.
  - No writes to 04_GOVERNANCE/
  - No hardcoded credentials
  - Fail closed on any constraint breach
  - Output valid Python code only


INSTRUCTIONS: Execute in Claude Code terminal. Return proposal to 08_IMPLEMENTATION_NOTES/.