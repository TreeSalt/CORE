# Mission: Real Task Progress Monitor — Not Ollama TTL

## Domain
03_ORCHESTRATION

## Model Tier
Sprint (9b)

## Description
Build a task progress monitor that shows ACTUAL mission progress,
not the misleading Ollama keep-alive TTL timer.

CONTEXT: ollama ps shows "4 minutes from now" which is the model eviction timer,
NOT the task completion estimate. This confused the operator into thinking a task
was still running when it had already finished.

REQUIREMENTS:
1. Read MISSION_QUEUE.json for IN_PROGRESS missions
2. Read started_at timestamp, compute elapsed time
3. Read historical mission completion times from past runs
4. Estimate remaining time based on average completion time for similar domain/tier
5. Display: mission_id, model, elapsed, estimated_remaining, progress_bar

ALLOWED IMPORTS: json, pathlib, datetime, statistics, sys
OUTPUT: scripts/task_monitor.py
TEST: Assert elapsed time computation is correct for a known timestamp.
