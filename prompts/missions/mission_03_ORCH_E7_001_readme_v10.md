# MISSION: README.md Updater for v10.0.0
DOMAIN: 03_ORCHESTRATION
TYPE: IMPLEMENTATION

## DELIVERABLE
File: scripts/update_readme.py

## REQUIREMENTS
- Read version from mantis_core/__init__.py
- Count ratified missions from 08_IMPLEMENTATION_NOTES/PROPOSAL_*.md
- Count escalations from ESCALATIONS/
- Update badge URLs with current counts
- Replace 'antigravity_harness' with 'mantis_core'
- Write updated README.md
- No external API calls
- Output valid Python only
