# MISSION: Domain Wiring Verification
DOMAIN: 07_INTEGRATION
TYPE: IMPLEMENTATION

## DELIVERABLE
File: 07_INTEGRATION/integration_domain/domain_wiring_test.py

## REQUIREMENTS
- For each domain in DOMAINS.yaml, verify: directory exists, __init__.py exists, at least one .py module
- Verify write_path matches actual directory structure
- Verify authorized_agents are valid model names
- Verify security_class is one of: INTERNAL, CONFIDENTIAL, PUBLIC
- Report any mismatches
- No external API calls
- Output valid Python only
