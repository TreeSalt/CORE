# MISSION: Bounty Engine — Submission Tracker
DOMAIN: 08_CYBERSECURITY
TASK: 07_SECURITY_E11_003_submission_tracker
TYPE: IMPLEMENTATION
VERSION: 1.0

## CONTEXT
Lifecycle management for vulnerability submissions, from discovery through payout.

## BLUEPRINT
1. Submission dataclass with status enum: DISCOVERED through REWARDED/REJECTED
2. Operations: create_submission, update_status, get_active, get_stats
3. Append-only history on every state transition
4. Persistence in state/bounty_submissions.json
5. generate_weekly_report() -> Markdown summary

## DELIVERABLE
File: mantis_core/security/submission_tracker.py

## CONSTRAINTS
- Python standard library (dataclasses, json, uuid, datetime)
- Append-only history
- Output valid Python only
