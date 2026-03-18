# Mission: Enhanced Session Dashboard — Mission Status + Red Team Summary

## Domain
05_REPORTING

## Model Tier
Sprint (9b)

## Description
Enhance the session status dashboard to include red team campaign results
alongside mission queue status.

REQUIREMENTS:
- Reads mission queue JSON and displays: total, completed, failed, pending
- Reads red team results from state/red_team/ and displays: campaigns run, total probes, anomalies found
- Reads run ledger and displays: current version, last drop timestamp, git status
- Outputs clean terminal table (no external libraries — use string formatting)
- Color output using ANSI escape codes

OUTPUT: scripts/session_dashboard.py
ALLOWED IMPORTS: json, pathlib, datetime, os, subprocess
TEST: Assert output contains "MISSIONS", "RED TEAM", "VERSION" section headers. Assert handles missing files gracefully (empty state).

## Acceptance Criteria
- Reads mission queue from configurable path
- Reads red team results from state/red_team/
- Reads run ledger for version info
- Displays clean ASCII table with ANSI colors
- Handles missing/empty files without crashing
- Shows timestamp of last update
