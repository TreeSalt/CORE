# MISSION: Prompt Injection Probe Generator
DOMAIN: 08_CYBERSECURITY
TYPE: IMPLEMENTATION

## DELIVERABLE
File: scripts/redteam/prompt_injection_probes.py

## REQUIREMENTS
- Generate mission files containing prompt injection attempts
- Vectors: "ignore previous instructions", role-play attacks, delimiter injection, system prompt extraction
- Each probe is a mission file that tries to make the LLM ignore constraints
- 20+ probes across 5 injection categories
- Output as JSON array of {probe_id, category, injection_text, expected_behavior}
- No external API calls
- Output valid Python only
