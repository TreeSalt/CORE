# MISSION: Session Summary Generator
DOMAIN: 05_REPORTING
TYPE: IMPLEMENTATION

## DELIVERABLE
File: scripts/session_summary_v2.py

## REQUIREMENTS
- read_queue(queue_path: str) -> dict: parse mission queue JSON file
- calculate_stats(queue: dict) -> dict: total, passed, failed, pass_rate, domains_covered
- generate_markdown(stats: dict, output_path: str) -> None: write session summary
- All file paths are function parameters
- Keep implementation under 100 lines
- No external calls of any kind
- Output valid Python only
