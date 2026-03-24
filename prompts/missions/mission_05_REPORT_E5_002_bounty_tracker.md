# MISSION: Bug Bounty Submission Tracker
DOMAIN: 05_REPORTING
TYPE: IMPLEMENTATION

## DELIVERABLE
File: scripts/bounty_tracker.py

## REQUIREMENTS
- Submission dataclass: id, platform, program, severity, status, submitted_date, reward
- load_submissions(json_path) -> list of Submission
- save_submission(submission, json_path) -> None: append to JSON file
- get_stats(submissions) -> dict: total, pending, accepted, rejected, total_reward
- generate_report(submissions, output_path) -> None: markdown summary
- All paths are function parameters
- No external calls
- Output valid Python only
