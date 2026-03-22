# MISSION: Credential Leak Scanner
DOMAIN: 08_CYBERSECURITY
TASK: implement_credential_leak_scanner
TYPE: IMPLEMENTATION

## CONTEXT
Build a scanner that checks all proposal files and mission outputs for credential patterns. Scan for: API keys (sk-*, AKIA*, Bearer tokens), passwords in assignment statements, .env file contents, private key material, and hardcoded connection strings.

## DELIVERABLE
File: scripts/redteam/credential_scanner.py

## REQUIREMENTS
- Scan a given directory recursively for credential patterns
- Support at least 10 distinct credential pattern types
- Output a report with file, line number, pattern type, and severity
- Return exit code 1 if any credentials found, 0 if clean
- No external API calls
- Output valid Python only
