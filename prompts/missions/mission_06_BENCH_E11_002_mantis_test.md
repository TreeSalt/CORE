# MISSION: Test Suite — MANTIS Trading Modules
DOMAIN: 06_BENCHMARKING
TASK: 06_BENCH_E11_002_mantis_test
TYPE: TEST
VERSION: 1.1

## CONTEXT
Tests for the E11 MANTIS trading modules. These modules live in the mantis_core package.

## EXACT IMPORTS (use these, not any other paths):
```python
from mantis_core.physics.regime_detector import RegimeDetector
from mantis_core.physics.trend_signal import TrendSignalGenerator
from mantis_core.physics.alpaca_harness import AlpacaHarness
from mantis_core.risk.position_sizer import PositionSizer
```

## BLUEPRINT
TestRegimeDetector: trending up/down detected, volatile detected, min bars enforced,
confidence range, fields populated (6 tests)

TestTrendSignal: buy in uptrend, hold in ranging, exit on regime shift, stop loss set,
never long in downtrend (5 tests)

TestPositionSizer: basic calc, zero equity raises, zero distance raises, max clamp,
never negative, crypto precision (6 tests)

TestAlpacaHarness: missing key raises, initializes with mock, max position enforced (3 tests)

Use numpy synthetic data. Mock Alpaca API with unittest.mock.
For API keys, use os.environ.get("ALPACA_API_KEY", "") — NEVER use string literals for keys.

## DELIVERABLE
File: 06_BENCHMARKING/tests/00_PHYSICS_ENGINE/test_mantis_trading.py

## CONSTRAINTS
- pytest, numpy, unittest.mock, os
- NEVER call real Alpaca API
- NEVER use hardcoded API key strings — always os.environ.get()
- Output valid Python only
