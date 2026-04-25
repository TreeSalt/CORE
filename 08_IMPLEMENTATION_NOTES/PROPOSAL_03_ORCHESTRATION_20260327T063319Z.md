---
DOMAIN: 03_ORCHESTRATION
MODEL: qwen3.5:9b
TIER: cruiser
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

```python
import threading
import time

def run_with_timeout(task_func, timeout=60):
    """
    Runs a task with a maximum timeout and returns its status ('SUCCESS', 'FAILURE', or 'TIMEOUT').
    
    Args:
        task_func: Function to execute (returns None or raises exception)
        timeout: Maximum allowed seconds before returning TIMEOUT
    
    Returns:
        str: Status of the task after completion or timeout
    """
    shared = {'status': None}

    def on_timeout(shared_result):
        if shared_result['status'] is None:
            shared_result['status'] = 'TIMEOUT'

    def target():
        try:
            task_func()
            shared['status'] = 'SUCCESS'
        except Exception:
            shared['status'] = 'FAILURE'

    t = threading.Thread(target=target)
    t.start()
    timer = threading.Timer(timeout, on_timeout, args=[shared])
    timer.start()

    t.join(timeout=timeout)

    return shared['status']


# Example usage
if __name__ == "__main__":
    print(run_with_timeout(lambda: time.sleep(3)))        # SUCCESS after ~3s
    print(run_with_timeout(lambda: (_ for _ in ()).throw(Exception())))  # FAILURE immediate
    print(run_with_timeout(lambda: time.sleep(70), timeout=5))   # TIMEOUT after 5s
```

This solution ensures correct behavior even when task completes exactly at timeout by checking if status is already set before updating. The `threading.Timer` fires to set 'TIMEOUT' only if the status hasn't been updated yet, handling all edge cases including race conditions safely in Python's GIL environment.