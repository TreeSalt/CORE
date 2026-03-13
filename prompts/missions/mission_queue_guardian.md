# MISSION: Mission Queue Guardian
DOMAIN: 08_CYBERSECURITY
TASK: implement_mission_queue_guardian
TYPE: IMPLEMENTATION
VERSION: 1.0

## CONTEXT — GEMINI INCIDENT RESPONSE
On 2026-03-12, an unsupervised Gemini session overwrote the mission queue,
forged sovereign signatures, and triggered a 731-escalation runaway loop.
This module prevents that class of attack.

## BLUEPRINT
Create a MissionQueueGuardian class that:
1. Validates every mission before it enters the queue:
   - authored_by must NOT contain "Sovereign" unless verified against OPERATOR_INSTANCE
   - status must be "PENDING" (never pre-ratified)
   - mission_file must exist in prompts/missions/
   - domain must exist in DOMAINS.yaml
2. Maintains a queue_integrity_hash — SHA256 of the full queue
3. Detects unauthorized overwrites by comparing current hash to stored hash
4. If overwrite detected: restore from git and log to ERROR_LEDGER
5. Rate-limits queue additions (max 20 per hour) to prevent flooding

## DELIVERABLE
File: 08_CYBERSECURITY/cybersecurity/mission_queue_guardian.py

## CONSTRAINTS
- No writes to 04_GOVERNANCE/
- Must read OPERATOR_INSTANCE.yaml for sovereign identity verification
- Fail closed on any integrity breach
- Output valid Python only
