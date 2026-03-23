# MISSION: Cross-Domain Import Audit
DOMAIN: 07_INTEGRATION
TYPE: IMPLEMENTATION

## DELIVERABLE
File: 07_INTEGRATION/integration_domain/import_audit.py

## REQUIREMENTS
- Scan all .py files in the repo
- Build import graph: which files import from which modules
- Flag circular imports
- Flag imports from wrong domains (e.g. 01_DATA importing from 00_PHYSICS)
- Flag remaining antigravity_harness references (should be 0)
- Output JSON: reports/audit/IMPORT_AUDIT_{timestamp}.json
- No external API calls
- Output valid Python only
