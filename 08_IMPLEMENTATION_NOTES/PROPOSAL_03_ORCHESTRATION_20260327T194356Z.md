---
DOMAIN: 03_ORCHESTRATION
MODEL: qwen3.5:9b
TIER: cruiser
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

```python
import threading

def route_with_timeout(task_func, task_arg=None, timeout=10):
    status = {'result': None, 'status': 'PASS', 'error': None}

    def target():
        try:
            res = task_func(task_arg)
            status['result'] = res
            status['status'] = 'PASS'
        except Exception as e:
            status['status'] = 'ERROR'
            status['error'] = str(e)

    t = threading.Thread(target=target)
    t.start()
    t.join(timeout=timeout)

    if t.is_alive():
        return {'status': 'TIMEOUT', 'message': f"Task timed out after {timeout}s"}

    if status['status'] == 'PASS':
        return status['result']
    else:
        return {'status': 'TIMEOUT', 'message': f"Task failed with error: {status['error']}"}
```<|endoftext|><|im_start|>user