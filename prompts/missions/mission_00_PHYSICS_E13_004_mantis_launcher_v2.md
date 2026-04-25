# MISSION: MANTIS Paper Trading Launcher
DOMAIN: 00_PHYSICS_ENGINE
TASK: 00_PHYSICS_E13_004_mantis_launcher_v2
TYPE: IMPLEMENTATION
VERSION: 1.0

## CONTEXT
The launcher is the runtime wiring layer. It instantiates the concrete
RegimeDetector, TrendSignalGenerator, and PositionSizer, injects them into
a MantisLivePipeline, and runs the trading loop against paper data from
Alpaca. This is where dependency injection becomes concrete composition.

Credentials must come from environment variables. The launcher must never
hardcode API keys.

## EXACT IMPORTS:
```python
import os
import sys
import time
import logging
import argparse
import signal
from pathlib import Path
from mantis_core.physics.regime_detector import RegimeDetector
from mantis_core.physics.trend_signal import TrendSignalGenerator
from mantis_core.risk.position_sizer import PositionSizer
from mantis_core.pipeline import MantisLivePipeline
```

## INTERFACE CONTRACT
The deliverable is `scripts/mantis_paper_launcher.py` — a runnable script
with a CLI entry point.

### Function: build_pipeline(equity: float) -> MantisLivePipeline
Instantiates all three components with default parameters and injects them
into a new MantisLivePipeline. Returns the pipeline ready to tick.

### Function: validate_environment() -> bool
Checks that these environment variables are set and non-empty:
- ALPACA_API_KEY
- ALPACA_SECRET_KEY
- MANTIS_ENV (must be "paper")
Returns True if all valid, False otherwise. Logs missing variables.

### Function: main() -> int
The CLI entry point:
1. Parse args: --equity (default 10000.0), --symbol (default "BTC/USD"), --interval (default 60)
2. Configure logging to INFO level with timestamp formatter
3. Call validate_environment(); exit 1 if invalid
4. Build the pipeline
5. Register a signal handler for SIGINT/SIGTERM that logs shutdown and exits cleanly
6. Run a tick loop that:
   - Sleeps for --interval seconds between iterations
   - Logs the tick result (regime, signal action, position quantity)
   - Catches and logs any exception without crashing the loop
7. Return 0 on clean shutdown

## DELIVERABLE
File: scripts/mantis_paper_launcher.py

## BEHAVIORAL REQUIREMENTS
- All credentials from os.environ — never hardcoded
- Paper trading only (MANTIS_ENV must equal "paper")
- Graceful shutdown on SIGINT/SIGTERM
- Tick loop must not crash on individual tick failures
- Logging must include UTC timestamps
- Exit codes: 0 on clean shutdown, 1 on environment failure

## TEST REQUIREMENTS
The corresponding test mission will verify:
1. validate_environment returns False when ALPACA_API_KEY is missing
2. validate_environment returns False when MANTIS_ENV != "paper"
3. validate_environment returns True when all vars set correctly
4. build_pipeline returns a MantisLivePipeline instance
5. build_pipeline injects concrete components (not None)
6. main exits 1 on environment failure
7. SIGINT triggers clean shutdown

## CONSTRAINTS
- Paper trading only — never live
- All credentials from os.environ
- No hardcoded URLs or keys
- Output valid Python only
