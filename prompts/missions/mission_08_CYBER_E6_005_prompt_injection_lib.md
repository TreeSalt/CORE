# MISSION: Prompt Injection Probe Library
DOMAIN: 08_CYBERSECURITY
TYPE: IMPLEMENTATION

## DELIVERABLE
File: scripts/redteam/prompt_injection_lib.py

## REQUIREMENTS
- generate_basic_injections(target_context) -> list of probe strings
- generate_jailbreak_probes(model_type) -> list of probe strings
- generate_data_exfil_probes(target_fields) -> list of probe strings
- categorize_response(response_text) -> dict: detected_leak, confidence, category
- All probes are for defensive testing only (constitutional constraint)
- No external calls
- Output valid Python only
