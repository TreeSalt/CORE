# MISSION: Supply Chain Dependency Auditor
DOMAIN: 08_CYBERSECURITY
TYPE: IMPLEMENTATION

## DELIVERABLE
File: scripts/redteam/supply_chain_audit.py

## REQUIREMENTS
- Parse requirements.txt for all dependencies
- Verify all have == version pinning and --hash entries
- Check typosquatting against common packages (requests, numpy, pandas, etc.)
- Flag unhashed packages as CRITICAL
- JSON report with package, version, pinned, hashed, risk_level
- No external API calls
- Output valid Python only
