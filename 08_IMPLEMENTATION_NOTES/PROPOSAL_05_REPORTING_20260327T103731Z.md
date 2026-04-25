---
DOMAIN: 05_REPORTING
MODEL: qwen3.5:4b
TIER: sprinter
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

```python
import json
import argparse
import sys
from pathlib import Path
from typing import Any, Dict, List


def load_queue(queue_path: str) -> List[Any]:
    """Read mission queue data from JSON file.
    
    Args:
        queue_path: Path to the JSON file containing mission data.
        
    Returns:
        The parsed JSON list of missions.
    """
    try:
        with open(queue_path, 'r') as f:
            data = json.load(f)
            
        # Ensure data is a list (defensive check based on description)
        if not isinstance(data, list):
            raise ValueError("Queue data must be a JSON array")
        
        return data
    except FileNotFoundError:
        print(f"Error: File {queue_path} not found.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON format in {queue_path}. Details: {e}")
        sys.exit(1)


def compute_stats(queue: List[Any]) -> Dict[str, Any]:
    """Compute mission statistics from the queue.
    
    Args:
        queue: List of mission objects (parsed JSON).
        
    Returns:
        Dictionary containing mission statistics including total count, ratified, escalated, pending, 
        pass_rate, and optionally escalated IDs for context generation.
    """
    stats = {
        "total": 0,
        "ratified": 0,
        "escalated": 0,
        "pending": 0,
        "pass_rate": 0.0,
    }

    # Handle empty queue
    if not queue:
        return stats

    total_missions = len(queue)
    
    for mission in queue:
        if isinstance(mission, dict):
            domain = mission.get("domain")
            status = mission.get("status")
            
            if status == "ratified":
                stats["ratified"] += 1
            elif status == "escalated":
                stats["escalated"] += 1
            elif status == "pending":
                stats["pending"] += 1
            
            # Track domains for reporting (implied need)
            if domain not in stats["domains"]:
                stats["domains"][domain] = 0
            stats["domains"][domain] += 1

        # Defensive check for non-dict items in queue
        else:
            pass # Treat as unknown or ignore based on strictness, but usually data should be dicts
            
    stats["total"] = total_missions
    
    if total_missions > 0:
        # Pass rate logic: Assuming Ratified and Escalated are considered 'passed' (approved/completed)
        successful = stats["ratified"] + stats["escalated"]
        stats["pass_rate"] = (successful / total_missions) * 100
    else:
        stats["pass_rate"] = 0.0
        
    # Adding escalated_ids to ensure function 3's output requirement is met, 
    # even if not explicitly listed in Returns description.
    # If the input format isn't specified, I'll assume it needs a simple ID or index if possible, 
    # but since it's complex, and 'escalated' status exists, let's try to infer.
    # Given "Include list of escalated missions with IDs", and no specific ID key is mentioned in stats description...
    # I will add the actual mission indices/IDs of escalated ones if possible (assuming index or id)
    # To satisfy function 3's text output, this is critical.
    
    escalated_ids = []
    for i, m in enumerate(queue):
        if isinstance(m, dict) and m.get("status") == "escalated":
            escalated_ids.append(i) # Assuming index is the proxy for ID or simple reference
            
    stats["escalated_ids"] = escalated_ids

    return stats


def generate_markdown(stats: Dict[str, Any]) -> str:
    """Generate markdown table of mission statistics.
    
    Args:
        stats: Dictionary containing mission data.
        
    Returns:
        Markdown string representing the statistics.
    """
    # Ensure we don't access missing keys safely
    total = stats.get("total", 0)
    ratified = stats.get("ratified", 0)
    escalated = stats.get("escalated", 0)
    pending = stats.get("pending", 0)
    pass_rate = stats.get("pass_rate", 0.0)

    # Generate table header and rows
    markdown_lines = ["### Mission Statistics Report", "\n| Metric | Value |", "----------|------"]
    
    markdown_lines.append(f"| Total Missions | {total} |")
    markdown_lines.append(f"| Ratified | {ratified} |")
    markdown_lines.append(f"| Escalated | {escalated} |")
    markdown_lines.append(f"| Pending | {pending} |")
    markdown_lines.append(f"| Pass Rate (Percentage) | {pass_rate:.2f}% |")
    
    # Add domain breakdown if available
    domains = stats.get("domains", {})
    if domains:
        markdown_lines.append("\n| Domain | Count |")
        markdown_lines.append("|---|---|")
        for domain, count in domains.items():
            markdown_lines.append(f"| {domain} | {count} |")
            
    return "\n".join(markdown_lines)


def execute_cli(args: Dict[str, Any]) -> int:
    """Execute main logic based on CLI arguments.
    
    Args:
        args: Dictionary containing command line arguments.
        
    Returns:
        Exit code (0 for success).
    """
    queue_path = str(args.get("queue"))
    output_file = Path(str(args.get("output")), "mission_stats.md")

    # Validate input path
    if not queue_path:
        print("Error: --queue flag is required.")
        return 1
    
    try:
        # Load data
        missions_queue = load_queue(queue_path)
        
        # Process stats
        stats = compute_stats(missions_queue)
        
        # Generate markdown
        report = generate_markdown(stats)
        
        # Write to file
        output_file.write_text(report)
        
        print(f"Report successfully generated: {output_file}")
        return 0
        
    except Exception as e:
        print(f"Error during execution: {e}")
        return 1


if __name__ == "__main__":
    # Set up arguments manually for clarity and to match Pythonic style (no complex parser setup)
    
    # Simulate argparse behavior by creating a dict from sys.argv
    raw_args = {}
    try:
        i = 1
        while i < len(sys.argv):
            if i + 1 < len(sys.argv):
                key, value = sys.argv[i], sys.argv[i+1]
                # Handle -- flag to separate args from values if needed (optional here for simplicity)
                # Assuming standard format: --key value
                raw_args[key] = value
                i += 2
            else:
                i += 1
    except Exception:
        raw_args["error"] = True

    # Call execute_cli with simulated arguments
    exit_code = execute_cli(raw_args)
    
    sys.exit(exit_code)
```