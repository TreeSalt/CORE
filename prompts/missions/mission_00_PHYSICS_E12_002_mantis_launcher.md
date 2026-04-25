# MISSION: MANTIS Paper Trading Launcher
DOMAIN: 00_PHYSICS_ENGINE
TASK: 00_PHYSICS_E12_002_mantis_launcher
TYPE: IMPLEMENTATION
VERSION: 1.0

## CONTEXT
CLI launcher for the MANTIS paper trading pipeline.

## EXACT IMPORTS:
```python
import argparse
import yaml
import logging
import signal
import sys
from pathlib import Path
from mantis_core.pipeline import MantisLivePipeline
```

## BLUEPRINT
Create `scripts/mantis_paper_trade.py`:

1. Parse args: --config (path to YAML), --dry-run, --symbol, --interval
2. Load config, override with CLI args
3. Validate: ALPACA_API_KEY and ALPACA_SECRET_KEY in environment
4. Initialize MantisLivePipeline
5. Register SIGINT handler for graceful shutdown
6. Run pipeline loop
7. On shutdown: print final state, save to `state/mantis_session.json`

Also create default config at `profiles/mantis_paper_btc.yaml`:
```yaml
symbol: BTC/USD
interval: 300
max_position_usd: 1000
risk_per_trade_pct: 1.0
regime_lookback: 20
trend_fast_period: 8
trend_slow_period: 21
```

## DELIVERABLE
File: scripts/mantis_paper_trade.py

## CONSTRAINTS
- Paper trading ONLY
- Fail-closed if API keys missing
- Output valid Python only
