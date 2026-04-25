# MISSION: Epoch Report Generator
DOMAIN: 05_REPORTING
TASK: 05_REPORT_E12_001_epoch_report
TYPE: IMPLEMENTATION
VERSION: 1.0

## CONTEXT
After each epoch completes, generate a structured markdown report summarizing
mission outcomes, timing, failures, and infrastructure metrics.

## EXACT IMPORTS:
```python
import json
from datetime import datetime, timezone
from pathlib import Path
from collections import Counter
```

## BLUEPRINT
Create `scripts/epoch_report.py`:

1. Reads `orchestration/MISSION_QUEUE.json`
2. Computes: total missions, ratified count, escalated count, retry count
3. Per-track breakdown (CORE_HARDENING, MANTIS_ALPHA, etc.)
4. Average time per mission, slowest mission, fastest mission
5. Infrastructure metrics: models used, tier distribution, SPLIT vs VRAM counts
6. Generates `docs/reports/EPOCH_{name}_{date}.md` with:
   - Mission table (id, status, time, tier, retries)
   - Track summary
   - Lessons learned (auto-detected from error patterns)
   - Recommendations for next epoch

## DELIVERABLE
File: scripts/epoch_report.py

## CONSTRAINTS
- Read-only access to queue and state files
- Output valid Python only
