# MISSION: sovereign_console_design
TYPE: ARCHITECTURE

## DELIVERABLE
File: docs/architecture/SOVEREIGN_CONSOLE.md

## SCOPE
Design for an interactive REPL that lets the sovereign triage CORE state
without manually editing JSON. Specify:
- Command set: audit, propose <mission>, approve <plan_id>, reject <plan_id>,
  history, queue-status, escalations, vault-tail
- UX flow diagrams for the most common scenarios
- Color scheme (CRITICAL red, WARNING yellow, INFO blue, SUCCESS green)
- Integration with the failure_pattern_library
- Every approval signed with vault key, logged to ledger
- Implementation language: Python (uses prompt_toolkit for the REPL)

## OUTPUT FORMAT
Markdown design doc with command reference, UX mockups (text-art),
state diagrams, and a small scenario walkthrough.
