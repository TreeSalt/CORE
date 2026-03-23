# MISSION: Configuration Validator
DOMAIN: 07_INTEGRATION
TYPE: IMPLEMENTATION

## DELIVERABLE
File: 07_INTEGRATION/integration_domain/config_validator.py

## REQUIREMENTS
- validate_domains(yaml_path: str) -> dict: check DOMAINS.yaml has required fields, no duplicate IDs
- validate_operator(yaml_path: str, init_path: str) -> dict: check version matches init file
- validate_queue(json_path: str) -> dict: check all missions have required fields
- validate_lockdown(json_path: str) -> dict: check valid JSON, enabled field is bool
- validate_all(repo_root: str) -> dict: run all validators, return consolidated report
- Only validate file contents — do not test network connectivity
- No external calls of any kind
- Output valid Python only
