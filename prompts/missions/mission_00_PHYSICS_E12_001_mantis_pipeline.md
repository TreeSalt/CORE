# MISSION: MANTIS Paper Trading Pipeline
DOMAIN: 00_PHYSICS_ENGINE
TASK: 00_PHYSICS_E12_001_mantis_pipeline
TYPE: IMPLEMENTATION
VERSION: 3.0

## EXACT IMPORTS:
```python
import os
import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from mantis_core.physics.regime_detector import RegimeDetector
from mantis_core.physics.trend_signal import TrendSignalGenerator
from mantis_core.risk.position_sizer import PositionSizer
```

## CONTEXT
E11 delivered four standalone trading modules: RegimeDetector, TrendSignalGenerator,
PositionSizer, and AlpacaHarness. This mission wires the first three into a
single pipeline class that processes market bars sequentially.

## REQUIREMENTS
Write `mantis_core/pipeline.py` containing a class `MantisLivePipeline` with:

- `__init__(self, symbol, max_position_usd, risk_pct)`: Store config, instantiate
  RegimeDetector, TrendSignalGenerator, and PositionSizer. Initialize a state dict.
- `tick(self, closes, current_price)`: Accept a numpy array of closing prices and
  the current price. Call RegimeDetector to classify the current regime. Pass the
  regime and price data to TrendSignalGenerator for a signal. If the signal suggests
  an entry, call PositionSizer to compute position size. Return a dict with the
  regime, signal, and computed size.
- `get_state(self)`: Return a copy of the internal state dict.

All API credentials must come from os.environ.get(), never hardcoded.

## DELIVERABLE
File: mantis_core/pipeline.py

## CONSTRAINTS
- Paper trading only — never real money
- Output valid Python only
