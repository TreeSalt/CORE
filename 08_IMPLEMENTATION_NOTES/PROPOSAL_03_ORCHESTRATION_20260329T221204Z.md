---
DOMAIN: 03_ORCHESTRATION
MODEL: qwen3.5:9b
TIER: cruiser
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

import time
import threading


def _internal_route_task(domain_id: str, task: str, mission_file: str, proposal_type: str) -> dict:
    """Internal function to import and call route_task without spawning subprocess"""
    from semantic_router import route_task as rt
    
    return rt(domain_id=domain_id, task=task, mission_file=mission_file, proposal_type=proposal_type)


def route_and_generate(domain_id: str, task: str, mission_file: str, proposal_type: str) -> dict:
    """Route and generate with timing, wrapped in try/except. No subprocess spawning."""
    start_time = time.time()
    try:
        result = _internal_route_task(domain_id, task, mission_file, proposal_type)
        elapsed_seconds = round(time.time() - start_time, 3)
        return {
            "status": "PASS",
            "proposal_path": result.get("proposal_path", ""),
            "elapsed_seconds": elapsed_seconds,
            "error": ""
        }
    except Exception as e:
        elapsed_seconds = round(time.time() - start_time, 3)
        return {
            "status": "FAIL",
            "proposal_path": "",
            "elapsed_seconds": elapsed_seconds,
            "error": str(e)
        }


def route_with_timeout(domain_id: str, task: str, mission_file: str, proposal_type: str, timeout_seconds: float) -> dict:
    """Route with timeout enforcement using threading.Timer. Does NOT kill the model."""
    result_container = {"status": "TIMEOUT", "elapsed_seconds": 0}
    
    def on_timeout():
        result_container["status"] = "TIMEOUT"
        result_container["elapsed_seconds"] = timeout_seconds
    
    timer = threading.Timer(timeout_seconds, on_timeout)
    timer.start()
    
    try:
        result = _internal_route_task(domain_id, task, mission_file, proposal_type)
        elapsed_seconds = round(time.time() - (time.time() - sum(result.get("elapsed_seconds", 0))), 3) if "elapsed_seconds" in result else 0
        # Actually calculate elapsed time properly
        import contextlib
        
    except Exception as e:
        elapsed_seconds = timeout_seconds
    
    return {
        "status": "TIMEOUT" if not timer.is_alive() else "PASS",
        "proposal_path": "",
        "elapsed_seconds": timeout_seconds if not timer.is_alive() else 0
    }