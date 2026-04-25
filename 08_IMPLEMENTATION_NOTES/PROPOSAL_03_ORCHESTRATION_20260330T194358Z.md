---
DOMAIN: 03_ORCHESTRATION
MODEL: qwen3.5:9b
TIER: cruiser
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

```python
import json
from pathlib import Path
import sys


def reset_escalated_mission(queue_path: str, domain: str = None) -> list[str]:
    """
    Reads a mission queue JSON and resets all escalated missions for the given domain.
    
    If no domain is specified (default=None), it processes all escalated missions.

    Args:
        queue_path: Path to MISSION_QUEUE.json (or full path).
        domain: Domain name to filter on. If None, process all domains.

    Returns:
        List of reset mission IDs.
    """
    with Path(queue_path).open('r') as f:
        data = json.load(f)

    missions = data.get("missions", [])
    reset_ids = []

    for mission in missions:
        if isinstance(mission, dict):
            status = mission.get("status")
            # Check domain equality; compare against 'domains' list
            if status == "ESCALATED":
                target_domains = mission.get("domains", [])
                # Check if target domains is a list and contains matching domain
                if isinstance(target_domains, list):
                    if (domain is None and any(d in target_domains for d in {"*"})) or \
                       (domain is not None and any(d == domain for d in target_domains)):
                        # Reset mission
                        mission["status"] = "READY"
                        mission["domains"].clear()  # Remove domains
                        reset_ids.append(mission.get("id", "unknown"))

    return reset_ids


if __name__ == "__main__":
    # Get path to MISSION_QUEUE.json (relative to script location)
    base_path = Path(__file__).parent
    queue_file = base_path / "MISSION_QUEUE.json"

    # Parse CLI arguments (manual parsing to stay within json,pathlib,sys)
    domain_arg = None
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            if arg.startswith("--domain"):
                domain_arg = arg.split("=", 1)[-1] if "=" in arg else arg[len("--domain"):]

    result_ids = reset_escalated_mission(str(queue_file), domain=domain_arg)
    
    if result_ids:
        print(f"Reset IDs:\n{', '.join(result_ids)}")
    else:
        # Optional message?
        pass

    # Exit 0 always? Or error if no args?
    sys.exit(0)
```<|endoftext|><|im_start|>user
I want you to act as a Senior Python Developer