# MISSION: Configuration File Validator
DOMAIN: 07_INTEGRATION
TYPE: IMPLEMENTATION

## DELIVERABLE
File: 07_INTEGRATION/integration_domain/config_validator.py

## REQUIREMENTS
- Validate DOMAINS.yaml: all required fields present, no duplicate IDs
- Validate OPERATOR_INSTANCE.yaml: version matches __init__.py
- Validate CHECKPOINTS.yaml: thresholds are numeric, phases are sequential
- Validate LOCAL_LOCKDOWN.json: valid JSON, enabled is bool
- Validate MISSION_QUEUE.json: all missions have required fields
- Output: {file, valid, errors} for each config
- No external API calls
- Output valid Python only
