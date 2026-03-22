# MISSION: Governance Bypass Test Suite
DOMAIN: 08_CYBERSECURITY
TASK: implement_governance_bypass_tests
TYPE: IMPLEMENTATION

## CONTEXT
Build a test suite that generates mission files attempting to bypass constitutional governance. Test vectors: forged "Authored_By: Sovereign" signatures, missions with "STATUS: RATIFIED" pre-set, missions instructing agents to write to 04_GOVERNANCE/, and missions that try to modify the governor seal.

## DELIVERABLE
File: scripts/redteam/governance_bypass_tests.py

## REQUIREMENTS
- Generate 10+ bypass probe missions across 4 attack categories
- Each probe includes expected benchmark gate that should catch it
- Verify the benchmark runner actually catches each bypass attempt
- Output as JSON array of {probe_id, attack_type, mission_text, expected_gate, expected_result}
- No external API calls
- Output valid Python only
