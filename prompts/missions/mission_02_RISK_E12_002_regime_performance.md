# MISSION: Regime Performance Tracker
DOMAIN: 02_RISK_MANAGEMENT
TASK: 02_RISK_E12_002_regime_performance
TYPE: IMPLEMENTATION
VERSION: 1.0

## CONTEXT
Track strategy performance broken down by market regime to identify which
regimes the strategy works in and which it should sit out.

## EXACT IMPORTS:
```python
import json
import statistics
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional
```

## BLUEPRINT
Create `mantis_core/risk/regime_performance.py` with:

1. `class RegimePerformanceTracker`:
   - `record_trade(regime, pnl, holding_period_minutes)`: accumulate stats per regime
   - `get_regime_stats(regime)`: return win_rate, avg_pnl, count, sharpe for that regime
   - `get_all_stats()`: return dict of all regimes with their stats
   - `should_trade(regime)`: return True if win_rate > 0.45 AND count > 10
   - `save(path)` / `load(path)`: persist to JSON
   - `generate_markdown_report()`: formatted regime comparison table

## DELIVERABLE
File: mantis_core/risk/regime_performance.py

## CONSTRAINTS
- Pure Python, no external dependencies beyond stdlib
- Output valid Python only
