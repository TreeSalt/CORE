# MISSION: Hallucination Probe Generator
DOMAIN: 08_CYBERSECURITY
TASK: implement_hallucination_probe_generator
TYPE: IMPLEMENTATION

## CONTEXT
Build a module that generates adversarial mission files designed to trick LLMs into importing non-existent libraries. The probes should cover: fake pip packages, misspelled real packages (e.g. 'numpy'), libraries that exist in other languages but not Python, and deprecated/removed stdlib modules.

## DELIVERABLE
File: scripts/redteam/hallucination_probes.py

## REQUIREMENTS
- Generate 20+ probe mission files targeting import hallucination
- Each probe includes the expected benchmark result (FAIL with reason)
- Output as JSON array of {probe_id, category, mission_text, expected_result}
- No external API calls
- Output valid Python only
