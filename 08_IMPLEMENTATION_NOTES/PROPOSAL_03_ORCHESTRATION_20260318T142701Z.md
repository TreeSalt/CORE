---
DOMAIN: 03_ORCHESTRATION
MODEL: qwen3.5:9b
TIER: sprinter
TYPE: IMPLEMENTATION
STATUS: RATIFIED
---

```python
# PROPOSAL FOR SCRIPT: scripts/core_cli.py
# FUNCTION: cmd_status()
# MODIFICATION: Integrate LOCKDOWN status section between GIT STATUS and MISSION QUEUE

from pathlib import Path
import json  # Already imported in core_cli.py, ensure available at top level

def cmd_status():
    """
    Generates the system status dashboard.
    UPDATED: Added Lockdown Status check.
    """
    
    # ... [Existing Code: GIT STATUS Section] ...
    
    # --- INSERTION POINT BETWEEN GIT STATUS AND MISSION QUEUE ---
    
    LOCKDOWN_PATH = Path("orchestration/LOCAL_LOCKDOWN.json")
    lockdown_output = ""

    if LOCKDOWN_PATH.exists():
        try:
            with open(LOCKDOWN_PATH, 'r') as f:
                config = json.load(f)
            
            is_locked = config.get('enabled', False)
            reason = config.get('reason', 'No reason specified')
            timestamp = config.get('timestamp', 'N/A')

            if is_locked:
                # Lock state: Red text + Lock Icon
                lockdown_output = "\033[1;31m🔒 LOCKDOWN ACTIVE\033[0m"
                lockdown_output += f" - Reason: {reason}"
                lockdown_output += f" | Updated: {timestamp}"
            else:
                # Unlock state: Green text + Unlock Icon
                lockdown_output = "\033[1;32m🔓 LOCKDOWN DISABLED\033[0m"
                lockdown_output += " (System Fully Operational)"

        except json.JSONDecodeError:
            # Fail closed on config corruption: Indicate warning state
            lockdown_output = "\033[93m⚠ CONFIGURATION PARSING ERROR\033[0m"
        except Exception:
            # Fail closed on any read error: Indicate potential risk but warn
            lockdown_output = "\033[93m⚠ LOCKDOWN STATUS CHECK FAILED (Assume Secure)\033[0m"
    else:
        # Config file missing: Warn but do not trigger lock automatically
        lockdown_output = "\033[93m⚠ CONFIG FILE MISSING (Defaulting to Check)\033[0m"

    # Print Lockdown Section
    if lockdown_output:
        print(f"\n  {lockdown_output}")

    # ... [Existing Code: MISSION QUEUE Section] ...
```