---
DOMAIN: 03_ORCHESTRATION
MODEL: qwen3.5:9b
TIER: cruiser
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

```python
import time
import threading


def route_and_generate(domain_id, task, mission_file, proposal_type) -> dict:
    """Route and generate a proposal with timing.
    
    Args:
        domain_id: The domain identifier
        task: The task description
        mission_file: Path to the mission file
        proposal_type: Type of proposal to generate
        
    Returns:
        dict with status, proposal_path, elapsed_seconds, error (if any)
    """
    from semantic_router.route import route_task
    
    start_time = time.time()
    
    try:
        result = route_task(domain_id=domain_id, task=task, mission_file=mission_file, 
                          proposal_type=proposal_type)
        
        elapsed = time.time() - start_time
        
        return {
            "status": "PASS",
            "proposal_path": result.get("proposal_path", ""),
            "elapsed_seconds": elapsed,
            "error": ""
        }
    except Exception as e:
        elapsed = time.time() - start_time
        
        return {
            "status": "FAIL",
            "proposal_path": "",
            "elapsed_seconds": elapsed,
            "error": str(e)
        }


def route_with_timeout(domain_id, task, mission_file, proposal_type, timeout_seconds) -> dict:
    """Route and generate with timeout enforcement using threading.Timer.
    
    Args:
        domain_id: The domain identifier
        task: The task description
        mission_file: Path to the mission file
        proposal_type: Type of proposal to generate
        timeout_seconds: Maximum time in seconds before timeout
        
    Returns:
        dict with status (TIMEOUT|PASS|FAIL), elapsed_seconds, etc.
    """
    from semantic_router.route import route_task
    
    completed = threading.Event()
    result_container = {'status': 'TIMEOUT', 'proposal_path': '', 'elapsed_seconds': 0, 'error': ''}
    
    def target():
        try:
            result = route_task(domain_id=domain_id, task=task, mission_file=mission_file, 
                              proposal_type=proposal_type)
            
            elapsed = time.time() - start_time
            
            result_container['status'] = "PASS"
            result_container['proposal_path'] = result.get("proposal_path", "")
            result_container['elapsed_seconds'] = elapsed
            result_container['error'] = ""
        except Exception as e:
            elapsed = time.time() - start_time
            
            result_container['status'] = "FAIL"
            result_container['proposal_path'] = ""
            result_container['elapsed_seconds'] = elapsed
            result_container['error'] = str(e)
        
        completed.set()
    
    timer = threading.Timer(timeout_seconds, target)
    timer.start()
    
    start_time = time.time()
    
    try:
        if not completed.wait(timeout=timeout_seconds):
            return {
                "status": "TIMEOUT",
                "proposal_path": "",
                "elapsed_seconds": timeout_seconds,
                "error": ""
            }
    except Exception:
        pass
    
    return result_container
```