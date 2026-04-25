---
DOMAIN: 03_ORCHESTRATION
MODEL: qwen3.5:9b
TIER: cruiser
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

The following implementation creates a thread-based system to manage "Light" and "Heavy" tasks across two "Lanes". Heavy tasks use a semaphore to ensure only one runs at a time, preventing resource conflicts. Non-heavy tasks are processed immediately in their respective worker threads.

```python
import threading
import queue
import subprocess
import logging
from pathlib import Path
import os
import sys

# Configure logging
logging.basicConfig(level=logging.INFO)

class HeavyLaneOrchestrator:
    def __init__(self, run_loop_path):
        self.run_loop_path = Path(run_loop_path).resolve() # Ensure path exists
        
        # Queues for tasks submitted to each lane
        self.cpu_queue = queue.Queue()
        self.gpu_queue = queue.Queue()
        
        # Locks representing resource access for each lane
        self.lane_cpu_lock = threading.Lock()
        self.lane_gpu_lock = threading.Lock()
        
        # Gate to enforce that only one Heavy task runs at a time
        self.heavy_gate = threading.Semaphore(1)
        
        self.running = False
        self.cpu_worker = None
        self.gpu_worker = None
        
    def start(self):
        self.running = True
        self.cpu_worker = threading.Thread(target=self._cpu_worker, daemon=True)
        self.gpu_worker = threading.Thread(target=self._gpu_worker, daemon=True)
        
        # Start the worker threads
        self.cpu_worker.start()
        self.gpu_worker.start()
        
    def stop(self):
        self.running = False

    def _worker_loop(self, worker_type, queue_obj):
        while self.running:
            try:
                # Get item with timeout to check running flag periodically
                item = queue_obj.get(timeout=1.0)
                
                # Handle StopSignal
                if item is None: 
                    break
                
                self._process_task(item, worker_type)
            except queue.Empty:
                pass # Timeout, continue loop
            
    def _cpu_worker(self):
        self._worker_loop('cpu', self.cpu_queue)

    def _gpu_worker(self):
        self._worker_loop('gpu', self.gpu_queue)

    def _process_task(self, item, worker_type):
        is_heavy = item.get('is_heavy', False)
        
        if is_heavy:
            # HEAVY TASK: Acquire gate and lane locks
            with self.heavy_gate: 
                try:
                    # Acquire both lanes. If one fails, release gate (handled by context manager)
                    with self.lane_cpu_lock:
                        with self.lane_gpu_lock:
                            logging.info(f"{worker_type} worker: Running HEAVY task on both lanes.")
                            
                            # Run the blocking script
                            # Use shell=False and check=True for safety, or False to ignore errors
                            subprocess.run(
                                str(self.run_loop_path), 
                                shell=(not self.run_loop_path.exists()), # Use shell only if path contains spaces/etc
                                check=False, 
                                stdout=subprocess.DEVNULL, 
                                stderr=subprocess.DEVNULL
                            )
                except Exception as e:
                    logging.error(f"{worker_type} worker: Error in heavy task: {e}")
        else:
            # LIGHT TASK: Process immediately (non-blocking)
            # Example: Simulate processing
            logging.info(f"{worker_type} worker: Processing LIGHT task quickly.")
            
    def submit_heavy(self, payload=None, queue='cpu'):
        """Submit a heavy task to the specified queue."""
        item = {
            'is_heavy': True, 
            'payload': payload or {},
            'worker_id': 'heavy' # For logging
        }
        
        if queue == 'cpu':
            self.cpu_queue.put(item)
        elif queue == 'gpu':
            self.gpu_queue.put(item)
        else:
            raise ValueError("Queue must be 'cpu' or 'gpu'")

    def submit_light(self, payload=None, queue='cpu'):
        """Submit a light task to the specified queue."""
        item = {
            'is_heavy': False, 
            'payload': payload or {}
        }
        
        if queue == 'cpu':
            self.cpu_queue.put(item)
        elif queue == 'gpu':
            self.gpu_queue.put(item)
        else:
            raise ValueError("Queue must be 'cpu' or 'gpu'")

# Example Usage
if __name__ == "__main__":
    # Determine run_loop_path (mock path for example)
    if len(sys.argv) > 1:
        run_loop_path = sys.argv[1]
    else:
        run_loop_path = "/usr/bin/run_loop" # Mock path
        
    orchestrator = HeavyLaneOrchestrator(run_loop_path=run_loop_path)
    
    try:
        orchestrator.start()
        
        # Submit heavy task to CPU queue (will block CPU lane and GPU lane)
        orchestrator.submit_heavy(payload={'task': 'heavy_cpu'}, queue='cpu')
        
        # Submit light task to CPU queue (non-blocking, processed immediately)
        orchestrator.submit_light(payload={'task': 'light_cpu'}, queue='cpu')
        
        # Submit heavy task to GPU queue (will block both lanes while running)
        orchestrator.submit_heavy(payload={'task': 'heavy_gpu'}, queue='gpu')
        
        # Let it run...
        import time; time.sleep(5) # Keep main thread alive
        
    finally:
        orchestrator.stop()
```

This code ensures that heavy tasks (blocking `run_loop_path` execution) are serialized and do not conflict with each other or themselves. Light tasks bypass the locks entirely, allowing concurrent processing on both lanes. The worker threads continuously process tasks from their respective queues until the orchestrator is stopped.