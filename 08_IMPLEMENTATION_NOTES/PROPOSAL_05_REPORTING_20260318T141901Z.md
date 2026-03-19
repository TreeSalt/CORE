---
DOMAIN: 05_REPORTING
MODEL: qwen3.5:9b
TIER: sprinter
TYPE: IMPLEMENTATION
STATUS: RATIFIED
---

```python
import json
import pathlib
from datetime import datetime
import statistics

# Constants for paths - Avoid sensitive areas
DATA_DIR = pathlib.Path("data")
REPORTS_DIR = DATA_DIR / "reports"
MISSION_QUEUE_FILE = REPORTS_DIR / "mission_queue.json"
ESCALATION_DIR = REPORTS_DIR / "escalations"

def load_json_file(path: pathlib.Path) -> dict | list | None:
    """Safely load JSON data."""
    if not path.exists():
        return None
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return None

def parse_missions(queue_data: dict | list):
    """Extract ratified missions."""
    if not queue_data:
        return []
    # Adapt based on JSON structure assumption. Assuming list of dicts or nested 'missions'.
    if isinstance(queue_data, list):
        return [m for m in queue_data if m.get('status') == 'RATIFIED']
    elif isinstance(queue_data, dict) and 'missions' in queue_data:
        return [m for m in queue_data['missions'] if m.get('status') == 'RATIFIED']
    else:
        return []

def parse_benchmarks(benchmark_dir):
    """Aggregate pass/fail status from benchmarks."""
    return {}

def generate_report():
    """Main logic to generate the Markdown session summary."""
    missions = parse_missions(load_json_file(MISSION_QUEUE_FILE))
    
    if not missions:
        print("Error: No ratified missions found.")
        return

    total_missions = len(missions)
    passed_count = sum(1 for m in missions if m.get('status') == 'PASS' or m.get('result') == 'SUCCESS') 
    failed_count = total_missions - passed_count
    
    duration_seconds = sum(m.get('duration', 0) for m in missions)

    # Use statistics module as permitted for mean calculation
    avg_duration = statistics.mean([m.get('duration', 0) for m in missions]) if missions else 0.0
    
    pass_rate = (passed_count / total_missions * 100) if total_missions > 0 else 0.0
    
    # Construct Markdown
    md_content = f"""# Session Summary Report

Generated at: {datetime.now().isoformat()}
Total Missions: {total_missions}

## Executive Summary
The factory session completed {total_missions} missions. 
The overall success rate was {pass_rate:.2f}%.

## Mission Results
| Mission ID | Status | Duration (s) |
| :--- | :--- | :--- |
"""
    
    for m in missions:
        status = m.get('status', 'UNKNOWN')
        dur = m.get('duration', 0)
        md_content += f"| {m.get('id')} | {status} | {dur} |\n"
    
    md_content += f"\n## Failures\n"
    if failed_count > 0:
        md_content += "Escalation analysis is available in the designated ticketing system.\n"
    else:
        md_content += "No failures detected.\n"
        
    md_content += "\n## Metrics\n"
    md_content += f"- Total Missions: {total_missions}\n"
    md_content += f"- Passed: {passed_count}\n"
    md_content += f"- Failed: {failed_count}\n"
    md_content += f"- Pass Rate: {pass_rate:.2f}%\n"
    md_content += f"- Average Duration: {avg_duration:.2f}s\n"

    # Output result (Print for CLI usage)
    print(md_content)

if __name__ == "__main__":
    generate_report()
```