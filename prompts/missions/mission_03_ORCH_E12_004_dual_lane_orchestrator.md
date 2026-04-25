# MISSION: Dual-Lane Orchestrator — GPU + CPU Parallel Execution
DOMAIN: 03_ORCHESTRATION
TASK: 03_ORCH_E12_004_dual_lane_orchestrator
TYPE: IMPLEMENTATION
VERSION: 3.0

## EXACT IMPORTS:
```python
import threading
import queue
import json
import logging
import time
import subprocess
from pathlib import Path
from datetime import datetime, timezone
```

## CONTEXT
The current orchestrator runs missions sequentially. With 8GB VRAM + 32GB RAM,
a 4B sprinter can run on GPU while a 9B cruiser runs on CPU simultaneously.
This dual-lane approach doubles throughput for mixed workloads.

## REQUIREMENTS
Write `scripts/dual_lane_orchestrator.py` containing a class `DualLaneOrchestrator`:

- Two PriorityQueues: one for GPU lane (sprinter tasks), one for CPU lane (cruiser tasks).
- A `dispatch(mission_dict, tier)` method that routes to the appropriate queue.
  Heavy-tier tasks go to GPU queue but must block the CPU lane until complete.
- Two worker methods (`gpu_worker`, `cpu_worker`) that pull from their queue and
  execute missions via subprocess. Results are stored in a thread-safe list.
- A `start()` method that launches both workers as daemon threads.
- A `stop()` method that signals workers to shut down gracefully.
- Shared state protected by threading.Lock.

## DELIVERABLE
File: scripts/dual_lane_orchestrator.py

## CONSTRAINTS
- Thread-safe queue and state management
- Heavy tier must block both lanes to prevent OOM
- Output valid Python only
