# Mission: 05_REPORT_E2_001_session_summary

## Domain
05_REPORTING

## Model Tier
Sprint (9b)

## Description
Build a session summary generator that produces a clean Markdown report
of everything accomplished in a factory run.

REQUIREMENTS:
1. Read MISSION_QUEUE.json for all RATIFIED missions
2. Read benchmark reports for pass/fail rates
3. Read escalation packets for failure analysis
4. Compute: total missions, pass rate, wall time, models used
5. Generate sections: Executive Summary, Mission Results, Failures, Metrics
6. Output clean Markdown suitable for LinkedIn or documentation

ALLOWED IMPORTS: json, pathlib, datetime, statistics
OUTPUT: scripts/session_summary.py
TEST: Assert output contains Executive Summary header. Assert pass rate is computed correctly.
