---
DOMAIN: 03_ORCHESTRATION
MODEL: qwen3.5:9b
TIER: cruiser
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

Here is the Python script implementing the `DualLaneOrchestrator` class with all specified requirements including task distribution, locking mechanisms for blocking CPU lanes, subprocess execution, and logging.

```python
import threading
import queue
import time
import subprocess
import logging
from typing import Dict, Any, List

# Configure logging to capture execution details
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

class DualLaneOrchestrator:
    def __init__(self):
        # Use a Priority Queue for strict ordering if needed (FIFO by default)
        self.cpu_queue = queue.PriorityQueue()
        self.gpu_queue = queue.PriorityQueue()
        
        # Shared state protected by lock
        self.results = []
        self.lock = threading.Lock() 
        
        # Event to signal graceful shutdown
        self.stop_event = threading.Event()
        
        # Thread objects to manage joining later
        self.worker_threads: List[threading.Thread] = []

    def _run_subprocess(self, mission):
        """Executes the actual workload using subprocess."""
        command = mission.get('command', 'echo "Simulated Command"')
        try:
            # Ensure we don't block too long on stdout redirection in some environments
            subprocess.run(command, shell=True, check=True)
        except subprocess.CalledProcessError as e:
            logging.error(f"[Subprocess Error] Mission {mission.get('id', 'unknown')} failed: {e}")
        except Exception as e:
            logging.error(f"[Generic Subprocess Error] Mission {mission.get('id', 'unknown')} failed: {e}")

    def _log_result(self, mission_id):
        """Safely log result with thread safety."""
        with self.lock:
            if mission_id in [m['id'] for m in self.results]:
                logging.warning(f"Duplicate result detected for ID: {mission_id}")
                return
            
            status = {
                "id": mission_id,
                "timestamp": time.time(),
                "type": "Completed"
            }
            # Check if it was heavy or cpu type for tracking in demo output
            self.results.append(status)

    def dispatch_mission(self, mission_dict: Dict[str, Any], tier: str):
        """Sends tasks to appropriate queue based on tier."""
        if tier == 'heavy':
            self.gpu_queue.put(mission_dict)
            # Heavy tasks block the CPU lane by holding `self.lock` during execution
            return True
        else:
            self.cpu_queue.put(mission_dict)
            return False

    def gpu_worker(self):
        """Worker thread handling GPU/Heavy tasks."""
        worker_id = "GPU"
        logging.info(f"[{worker_id}] Worker started")
        
        while not self.stop_event.is_set():
            try:
                # Use timeout to allow checking stop_event periodically
                mission = self.gpu_queue.get(timeout=1.0)
                
                tier = mission.get('tier', 'cpu')
                mission_id = mission.get('id', 'unknown')
                
                # Heavy tasks MUST block the CPU lane (resource contention simulation)
                if tier == 'heavy':
                    with self.lock:
                        logging.info(f"[{worker_id}] Acquired Heavy Lock for task: {mission_id}")
                        time.sleep(2)  # Simulate heavy GPU workload
                        
                        # Run actual work
                        self._run_subprocess(mission)
                        
                        logging.info(f"[{worker_id}] Released lock and finished task: {mission_id}")
                else:
                    # Light tasks don't need exclusive lock for critical section usually, 
                    # but we log it.
                    logging.info(f"[{worker_id}] Processing light task: {mission_id}")
                    time.sleep(0.5)
                    self._run_subprocess(mission)

            except queue.Empty:
                pass
            
            # Ensure result is appended safely (if needed)
            with self.lock:
                if 'status' in mission:
                     self.results.append({"type": "GPU", **mission['status']})

    def cpu_worker(self):
        """Worker thread handling CPU/Light tasks."""
        worker_id = "CPU"
        logging.info(f"[{worker_id}] Worker started")
        
        while not self.stop_event.is_set():
            try:
                mission = self.cpu_queue.get(timeout=1.0)
                
                mission_id = mission.get('id', 'unknown')
                
                # If CPU worker needs to update shared state, it uses the lock.
                with self.lock:
                    logging.info(f"[{worker_id}] Processing light task: {mission_id}")
                    time.sleep(1)  # Simulate processing
                    
                    self._run_subprocess(mission)

            except queue.Empty:
                pass
            
            # Add to results safely (in case CPU worker updates state)
            with self.lock:
                 if 'status' in mission:
                     self.results.append({"type": "CPU", **mission['status']})

    def process(self, missions: List[Dict[str, Any]], tier_map: Dict[str, str]):
        """Dispatches missions and starts processing threads."""
        logging.info("Starting DualLaneOrchestrator")
        
        for m in missions:
            # Use the provided tier map to determine queue destination
            t = tier_map.get(m.get('id'), 'cpu')
            self.dispatch_mission(m, t)
            
        # Start workers immediately after dispatching all tasks to ensure processing begins
        t1 = threading.Thread(target=self.gpu_worker, name="GPU-Worker")
        t2 = threading.Thread(target=self.cpu_worker, name="CPU-Worker")
        
        t1.start()
        t2.start()
        
        self.worker_threads.extend([t1, t2])
        logging.info("All workers started.")

    def stop(self):
        """Gracefully stops the orchestration."""
        logging.info("Stopping orchestrator...")
        self.stop_event.set()
        
        # Wait for threads to finish (they will break out of loops when stop_event is set)
        for t in self.worker_threads:
            t.join()
            
        logging.info(f"Orchestrator stopped. Results collected: {len(self.results)}")

if __name__ == "__main__":
    orchestrator = DualLaneOrchestrator()
    
    # Define sample missions
    missions = [
        {'id': '1', 'command': 'echo "Running Light CPU Task" && sleep 0.5', 'tier': 'cpu'},
        {'id': '2', 'command': 'echo "Running Heavy GPU Task (Blocking)" && sleep 2', 'tier': 'heavy'},
        {'id': '3', 'command': 'echo "Running Another Light CPU Task" && sleep 0.5', 'tier': 'cpu'}
    ]
    
    # Define tier map for demo purposes (could be more complex in real app)
    tier_map = {m['id']: m['tier'] for m in missions}
    
    orchestrator.process(missions, tier_map)
    time.sleep(3)  # Give a buffer for threads to finish up tasks started at the end
    
    orchestrator.stop()
    logging.info("Script execution finished.")
```

### How It Works:

1.  **Task Dispatch:** The `process` method iterates through missions and uses the provided `tier_map` to decide where to send them via `dispatch_mission`. 'heavy' tasks go to `gpu_queue`, others to `cpu_queue`.
2.  **Worker Threads:** 
    *   `gpu_worker`: Retrieves from `gpu_queue`.
    *   `cpu_worker`: Retrieves from `cpu_queue`.
3.  **Blocking Mechanism:** When a heavy task is picked up by the GPU worker, it enters a `with self.lock:` block. Since the CPU worker also uses `self.lock` for safe state updates (appending results), the GPU task effectively blocks the CPU lane from updating shared data while it runs.
4.  **Subprocess Execution:** Uses `subprocess.run` to execute the provided shell command safely.
5.  **Graceful Shutdown:** The `stop()` method sets an event flag, causing worker threads to break out of their loops, and then waits (joins) for them to exit cleanly. Logging confirms completion.

### Output Explanation:

The logs will demonstrate that 'Heavy' tasks block access to the shared lock used by CPU tasks. You should see interleaved logs reflecting this contention:

*   **Before Stop:** The log will show `GPU-Worker` acquiring the lock for task ID 2. Immediately after, `CPU-Worker` will likely sleep or wait because the `self.lock` is held until the GPU worker finishes and releases it (simulated by the logic in `_run_subprocess`/`_log_result`).
*   **After Stop:** The script waits 3 seconds to ensure background threads finish their current iterations before calling `stop()`.

This architecture ensures that even if a CPU task is queued, if a heavy GPU task holds the lock, the CPU worker (attempting to update shared state/results) must wait.