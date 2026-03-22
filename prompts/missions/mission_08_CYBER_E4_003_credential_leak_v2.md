# MISSION: Credential Leak Scanner (Retry)
DOMAIN: 08_CYBERSECURITY
TASK: implement_credential_leak_scanner
TYPE: IMPLEMENTATION

## CONTEXT
Previous attempt ESCALATED. Build a scanner that checks proposal files and mission outputs for credential patterns: API keys (sk-*, AKIA*, Bearer), passwords in assignments, .env contents, private key material, hardcoded connection strings.

## DELIVERABLE
File: scripts/redteam/credential_scanner.py

## REQUIREMENTS
- Scan directory recursively for 10+ credential pattern types
- Output report: file, line, pattern type, severity
- Return exit code 1 if found, 0 if clean
- No external API calls, no hardcoded credentials in the scanner itself
- Output valid Python only
