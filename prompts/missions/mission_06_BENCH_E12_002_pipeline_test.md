# MISSION: Test Suite — MANTIS Pipeline Integration
DOMAIN: 06_BENCHMARKING
TASK: 06_BENCH_E12_002_pipeline_test
TYPE: TEST
VERSION: 1.0

## CONTEXT
Integration tests for the MANTIS paper trading pipeline.

## EXACT IMPORTS:
```python
from mantis_core.pipeline import MantisLivePipeline
from mantis_core.physics.regime_detector import RegimeDetector
from mantis_core.physics.trend_signal import TrendSignalGenerator
from mantis_core.risk.position_sizer import PositionSizer
from mantis_core.risk.trade_journal import TradeJournal, TradeEntry
from mantis_core.risk.regime_performance import RegimePerformanceTracker
```

## BLUEPRINT
TestMantisLivePipeline: config loads, tick processes bar, signal generates order,
position sized correctly, state serializable (5 tests)

TestTradeJournal: log entry, close trade updates pnl, open trades filtered,
report stats correct, csv export works (5 tests)

TestRegimePerformance: record trade, stats per regime, should_trade threshold,
save/load roundtrip, markdown report format (5 tests)

Use numpy synthetic data. Mock Alpaca API with unittest.mock.
For API keys, use os.environ.get("ALPACA_API_KEY", "") — NEVER string literals.

## DELIVERABLE
File: 06_BENCHMARKING/tests/00_PHYSICS_ENGINE/test_mantis_pipeline.py

## CONSTRAINTS
- pytest, numpy, unittest.mock, os, tempfile
- NEVER call real Alpaca API
- Output valid Python only
