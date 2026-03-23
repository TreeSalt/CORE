# MISSION: CHANGELOG.md Generator
DOMAIN: 03_ORCHESTRATION
TYPE: IMPLEMENTATION

## DELIVERABLE
File: scripts/generate_changelog.py

## REQUIREMENTS
- Parse git log for conventional commits (feat:, fix:, refactor:)
- Group by date range
- Highlight BREAKING changes
- Include migration notes for antigravity_harness -> mantis_core
- Write CHANGELOG.md
- No external API calls
- Output valid Python only
