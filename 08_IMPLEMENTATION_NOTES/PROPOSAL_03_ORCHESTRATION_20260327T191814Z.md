---
DOMAIN: 03_ORCHESTRATION
MODEL: qwen3.5:9b
TIER: cruiser
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

```python
import threading


def route(timeout_seconds: int | float, *args, **kwargs) -> Any:
    """
    Executes route_task(*args, **kwargs) within a specified timeout period using a daemon thread.
    
    If the task completes successfully within the time limit, its return value is returned.
    If an exception occurs during execution (including timeout), it raises an appropriate exception 
    with informative messages.
    
    :param timeout_seconds: Maximum duration in seconds before raising TimeoutError.
    :return: The result of route_task on success.
    :raises Exception: Any exception raised by route_task, or a custom TimeoutError if the task doesn't finish in time.
    """
    
    # Shared result container to store outcome safely across threads
    results = {'result': None, 'error': None}

    def worker():
        try:
            res = route_task(*args, **kwargs)
            results['result'] = res
        except Exception as e:
            results['error'] = str(e)

    # Launch task in a daemon thread to prevent hanging the main program
    thread = threading.Thread(target=worker, daemon=True)
    thread.start()

    # Block with timeout; join will return as soon as thread finishes or timeout expires
    thread.join(timeout=timeout_seconds)

    if thread.is_alive():
        raise TimeoutError(f"Route task timed out after {timeout_seconds} seconds")

    error = results.get('error')
    if error:
        raise Exception(error)

    return results['result']
```