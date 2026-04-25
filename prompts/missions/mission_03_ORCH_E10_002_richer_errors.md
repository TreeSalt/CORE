# MISSION: Richer Error Context in Escalation Packets

Write a Python module: scripts/enrich_escalation.py

This module enhances escalation packet files with actual error details
instead of just "see ERROR_LEDGER".

Write these functions:

1. extract_last_error(error_ledger_path, domain_id) -> str
   - Reads docs/ERROR_LEDGER.md
   - Finds the most recent error entry for the given domain
   - Returns the full error text including reason and recovery suggestion

2. enrich_packet(escalation_path, error_text) -> None
   - Reads the escalation markdown file
   - Appends a "## Root Cause" section with the actual error text
   - Writes the enriched file back

3. enrich_all_pending(escalations_dir, error_ledger_path) -> int
   - Finds all ESCALATION_*.md files without a "## Root Cause" section
   - Enriches each one
   - Returns count of enriched files

Use only pathlib and re. No external packages.
