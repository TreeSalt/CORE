# MISSION: COUNCIL_CANON Dedup Fix
DOMAIN: 03_ORCHESTRATION
TASK: fix_council_canon_dedup
TYPE: IMPLEMENTATION

## CONTEXT
The build.py forge script produces duplicate entries in COUNCIL_CANON.yaml. Fix the dedup logic so each canon entry appears exactly once.

## DELIVERABLE
File: scripts/canon_dedup_fix.py

## REQUIREMENTS
- Read docs/ready_to_drop/COUNCIL_CANON.yaml
- Remove duplicate entries (by key)
- Write back deduplicated YAML
- Log how many duplicates removed
- Can also be integrated as a pre-step in make_drop_packet.py
- No external API calls
- Output valid Python only
