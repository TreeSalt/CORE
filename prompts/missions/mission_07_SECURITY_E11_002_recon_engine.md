# MISSION: Bounty Engine — Recon Engine
DOMAIN: 08_CYBERSECURITY
TASK: 07_SECURITY_E11_002_recon_engine
TYPE: IMPLEMENTATION
VERSION: 1.0

## CONTEXT
After target scraping, the recon engine performs automated reconnaissance against
in-scope AI/ML targets. Leverages CORE's Red Team Engine patterns for probe design.

## BLUEPRINT
1. ReconProfile dataclass: target, endpoints, technologies, input surfaces,
   potential vectors, risk score
2. AI-specific recon: detect model providers, identify prompt injection surfaces,
   detect system prompt leakage, map input-output chains
3. run_recon(target) -> ReconProfile, respecting scope boundaries
4. rank_targets by risk_score descending, filter below 0.3
5. All requests logged to state/recon_log.json

## DELIVERABLE
File: mantis_core/security/recon_engine.py

## CONSTRAINTS
- requests for HTTP
- NEVER send malicious payloads — information gathering only
- MUST respect program scope
- Rate limit: 5 seconds between requests per target
- Output valid Python only
