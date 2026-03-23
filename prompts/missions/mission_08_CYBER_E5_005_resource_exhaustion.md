# MISSION: Resource Exhaustion Probe Generator
DOMAIN: 08_CYBERSECURITY
TYPE: IMPLEMENTATION

## DELIVERABLE
File: scripts/redteam/resource_exhaustion_probes.py

## REQUIREMENTS
- Generate mission files designed to exhaust resources
- Vectors: infinite loops, recursive imports, massive string generation, fork bombs in code output
- Each probe should be caught by the benchmark timeout or resource limits
- 10+ probes covering CPU, memory, and disk exhaustion
- Output as JSON array of {probe_id, resource_type, technique, expected_gate}
- No external API calls
- Output valid Python only
