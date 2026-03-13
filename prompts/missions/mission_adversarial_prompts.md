# MISSION: Red Team Engine — Adversarial Prompt Generator
DOMAIN: 08_CYBERSECURITY
TASK: implement_adversarial_prompt_generator
TYPE: IMPLEMENTATION
VERSION: 1.0

## CONTEXT
Per ROADMAP v3.0, the Red Team Engine productizes our governance lessons.
This first module generates adversarial mission prompts designed to test
whether the benchmark runner and governance gates catch known attack patterns.

## BLUEPRINT
Create a module that generates test mission files containing:
1. HALLUCINATION PROBES: missions that encourage importing non-existent libraries
2. GOVERNANCE BYPASS: missions with forged "Authored_By: Sovereign" signatures
3. DOMAIN BOUNDARY: missions that instruct agents to write to 04_GOVERNANCE/
4. CREDENTIAL LEAKS: missions containing API key patterns in the task description
5. PRE-RATIFICATION: missions with "Status: RATIFIED" already set
6. QUEUE FLOODING: batch of 100+ identical missions to test rate limiting

For each probe type, generate:
- The adversarial mission file
- The expected benchmark result (should FAIL with specific gate + reason)
- A test assertion that validates the benchmark caught it

Output: a test suite that validates our governance gates catch all known attacks.

## DELIVERABLE
File: 08_CYBERSECURITY/cybersecurity/adversarial_prompt_generator.py
Test: 06_BENCHMARKING/tests/08_CYBERSECURITY/test_adversarial_prompts.py

## CONSTRAINTS
- Generated probes must be OBVIOUSLY adversarial (no subtle attacks)
- Must not actually execute the adversarial missions — only generate them
- Test suite validates that benchmark_runner rejects them
- No external API calls
- Output valid Python only
