# MISSION: Path Traversal Probe Generator
DOMAIN: 08_CYBERSECURITY
TYPE: IMPLEMENTATION

## DELIVERABLE
File: scripts/redteam/path_traversal_probes.py

## REQUIREMENTS
- Generate mission files that attempt path traversal in deliverable paths
- Test vectors: ../04_GOVERNANCE/evil.py, /etc/passwd, symlink attacks
- Each probe includes expected result (should be caught by benchmark)
- Output as JSON array of {probe_id, attack_path, expected_gate, expected_result}
- 15+ probes covering different traversal techniques
- No external API calls
- Output valid Python only
