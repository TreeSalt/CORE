---
DOMAIN: 05_REPORTING
MODEL: qwen3.5:9b
TIER: sprinter
TYPE: IMPLEMENTATION
STATUS: RATIFIED
---

```python
import json
import time
import sys
from datetime import datetime
import urllib.request
import os

# ANSI Color Codes
COLOR_RESET = "\033[0m"
COLOR_GREEN = "\033[92m"
COLOR_YELLOW = "\033[93m"
COLOR_BLUE = "\033[94m"
COLOR_RED = "\033[91m"

def cmd_status(args):
    """
    Updated status command with --live flag for real-time factory monitoring.
    Requires: MISSION_QUEUE.json access, Ollama API connectivity.
    """
    
    # Flag Check
    if not hasattr(args, 'live') or not args.live:
        # Execute standard status logic (placeholder)
        return None

    # Configuration Constants
    OLLAMA_HOST = "http://localhost:11434"
    MISSION_QUEUE_PATH = os.path.join(os.path.dirname(__file__), "..", "MISSION_QUEUE.json")
    
    def get_model_info():
        """Query Ollama API for loaded models."""
        try:
            url = f"{OLLAMA_HOST}/api/ps"
            response = urllib.request.urlopen(url, timeout=5)
            data = json.loads(response.read().decode("utf-8"))
            
            if not data.get("models"):
                return { "status": COLOR_RED + "No model loaded" + COLOR_RESET }
            
            model = data["models"][0]
            # Human readable size calculation (KB, MB, GB)
            size_bytes = model.get("size", 0)
            if size_bytes > 1024**3:
                size_str = f"{size_bytes / (1024**3):.2f} GB"
            elif size_bytes > 1024**2:
                size_str = f"{size_bytes / (1024**2):.2f} MB"
            else:
                size_str = f"{size_bytes} B"
            
            # Extract available details, fallback defaults for missing fields
            details = model.get("details", {})
            quantization = details.get("quantization_level", "Unknown")
            context = details.get("context_window", "N/A (Not exposed in /api/ps)") # Context might require specific model config
            
            return {
                "model_name": model.get("name", "N/A"),
                "size": size_str,
                "quantization": quantization,
                "context": context
            }
        except Exception:
            # Fail closed on API breach (network/auth) without leaking secrets
            return {"status": COLOR_RED + "Ollama API Unreachable or Auth Failed" + COLOR_RESET}

    def get_mission_info():
        """Read MISSION_QUEUE.json for IN_PROGRESS mission."""
        try:
            with open(MISSION_QUEUE_PATH, 'r') as f:
                data = json.load(f)
            
            mission = None
            if isinstance(data, list):
                for m in data:
                    if m.get("status") == "IN_PROGRESS":
                        mission = m.get("name", m.get("mission"))
                        break
            elif isinstance(data, dict):
                mission = data.get("name")
            
            return COLOR_GREEN + f"Mission: {mission}" if mission else COLOR_YELLOW + "No active mission in queue" + COLOR_RESET
        except Exception:
            # Fail closed on file read error
            return "MISSION_QUEUE.json not found or readable"

    # Start Time Tracking
    start_time = time.time()
    interval = 3.0 # Seconds per refresh
    
    print(COLOR_BLUE + f"[ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ] Initializing Live Monitor...\n" + COLOR_RESET)
    
    while args.live: # Loop condition based on external signal or interrupt
        try:
            # Update Mission and Model Info
            mission_str = get_mission_info()
            model_str = get_model_info()
            
            # Calculate Elapsed Time
            elapsed_time = datetime.now() - start_time
            
            # Render Output
            print(COLOR_RESET)
            print(f"┌── [{COLOR_GREEN}RUNNING{COLOR_RESET}]")
            print(f"│ {mission_str}")
            print(f"│ {model_str}")
            print(f"└── Elapsed: {elapsed_time.strftime('%H:%M:%S')}")
            
            # Delay before next loop
            time.sleep(interval)
        except Exception as e:
            # Fail closed: Handle gracefully, don't dump raw stack trace to screen
            print(f"\n\033[91mError fetching status: {e}\033[0m", file=sys.stderr)

if __name__ == "__main__":
    # Mock args object for demonstration of implementation
    class Args:
        live = True
    cmd_status(Args())
```