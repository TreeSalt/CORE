# MISSION: Router API Wrapper

Write a Python module: orchestration/router_api.py

This module wraps route_task() as a direct Python function call
so run_loop.py can import and call it instead of spawning a subprocess.

Write these functions:

1. route_and_generate(domain_id, task, mission_file, proposal_type) -> dict
   - Returns {"status": "PASS"|"FAIL", "proposal_path": str, "elapsed_seconds": float, "error": str}
   - Imports route_task from semantic_router directly
   - Wraps the call in a try/except with timing
   - No subprocess spawning

2. route_with_timeout(domain_id, task, mission_file, proposal_type, timeout_seconds) -> dict
   - Same as above but uses threading.Timer to enforce timeout
   - If timeout reached, returns {"status": "TIMEOUT", "elapsed_seconds": timeout_seconds}
   - Does NOT kill the model — lets it finish but stops waiting

Use only stdlib imports (threading, time, importlib). No external packages.
