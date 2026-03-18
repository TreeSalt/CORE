# Mission: Decision Log Formatter — Clean Markdown from Raw JSON

## Domain
04_GOVERNANCE

## Model Tier
Flash (4b)

## Description
Build a formatter that converts raw decision log JSON entries into clean,
readable Markdown for the governance audit trail.

OUTPUT: scripts/decision_log_formatter.py
ALLOWED IMPORTS: json, typing, pathlib, datetime
TEST: Feed 3 raw decision entries. Assert output Markdown has 3 ## headers. Assert timestamps are formatted as ISO 8601.

## Acceptance Criteria
- format_decision(entry_dict) returns Markdown string
- format_log(entries_list) returns full Markdown document
- Timestamps formatted as ISO 8601
- Decision rationale preserved verbatim
- Status shown with emoji indicators (✅ RATIFIED, ❌ REJECTED, ⏳ PENDING)
