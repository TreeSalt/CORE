# MISSION: Queue Flood Defense
DOMAIN: 08_CYBERSECURITY
TASK: implement_queue_flood_defense
TYPE: IMPLEMENTATION

## CONTEXT
Build a defense module that prevents mission queue flooding. An attacker (or malfunctioning agent) could inject hundreds of missions to overwhelm the factory. The defense should enforce: max queue size limit, rate limiting on mission additions, duplicate detection, and domain-balance enforcement (no single domain can exceed 50% of queue).

## DELIVERABLE
File: scripts/redteam/queue_guardian.py

## REQUIREMENTS
- Validate MISSION_QUEUE.json against flood rules before accepting new missions
- Configurable max queue size (default 50)
- Reject duplicates by mission file hash
- Enforce domain balance (no domain > 50% of queue)
- Log all rejections with reason
- No external API calls
- Output valid Python only
