# MISSION: MANTIS Live Pipeline (Dependency Injection)
DOMAIN: 00_PHYSICS_ENGINE
TASK: 00_PHYSICS_E13_003_mantis_pipeline_v2
TYPE: IMPLEMENTATION
VERSION: 1.0

## CONTEXT
The previous E12 attempt at this mission failed because it imported three
modules that did not exist on disk. This v2 uses dependency injection: the
pipeline receives its detector, signal generator, and sizer as constructor
parameters rather than importing concrete classes. This makes the pipeline
testable in isolation with mock components and decouples it from any
specific implementation.

E13_001, E13_002, and E13_003 build the concrete components. E13_004 (this
mission) wires them into a pipeline. E13_005 (next) creates the runtime
launcher.

## EXACT IMPORTS:
```python
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional
```

## INTERFACE CONTRACT
The deliverable is `mantis_core/pipeline.py` containing:

### Dataclass: PipelineState
Frozen dataclass holding the latest state:
```
last_regime: Optional[str]
last_signal_action: Optional[str]
last_quantity: Optional[float]
last_tick_timestamp: Optional[datetime]
total_ticks: int
total_signals_generated: int
```

### Dataclass: TickResult
Frozen dataclass returned by each tick():
```
regime: Any                # RegimeState from detector
signal: Any                # TradeSignal from signal generator
position: Optional[Any]    # PositionSize from sizer (None if no entry)
timestamp: datetime
```

### Class: MantisLivePipeline
Constructor signature:
```
__init__(self, regime_detector, signal_generator, position_sizer, equity, symbol="BTC/USD")
```

The constructor:
1. Stores all four dependencies and configuration
2. Initializes a PipelineState with zeros and None
3. Does NOT import any concrete RegimeDetector/TrendSignalGenerator/PositionSizer
4. Validates equity > 0, raises ValueError otherwise

Method: `tick(self, closes, highs, lows, current_price) -> TickResult`

The method must:
1. Call self.regime_detector.classify_regime(closes, highs, lows) → RegimeState
2. Extract atr from the RegimeState
3. Call self.signal_generator.generate_signal(closes, current_price, regime_str, atr) → TradeSignal
4. If signal.action is ENTER_LONG or ENTER_SHORT:
   a. Call self.position_sizer.size_position(equity, current_price, signal.stop_loss) → PositionSize
   b. Store position in TickResult
5. Otherwise position is None
6. Update internal state: increment total_ticks, update last_* fields
7. Return populated TickResult

Method: `get_state(self) -> PipelineState`
Returns a copy of the current internal state.

## DELIVERABLE
File: mantis_core/pipeline.py

## BEHAVIORAL REQUIREMENTS
- Pure orchestration: zero indicator math, zero direct numpy usage
- Dependency injection: never import concrete component classes
- Deterministic given deterministic dependencies
- No file I/O, no network calls
- State updates must be visible via get_state()

## TEST REQUIREMENTS
The corresponding test mission will verify (using mock dependencies):
1. Constructor raises ValueError for non-positive equity
2. tick() calls all three dependencies with correct arguments
3. tick() returns TickResult with populated regime and signal
4. tick() includes position when signal action is ENTER_LONG/SHORT
5. tick() returns position=None when signal action is NO_ACTION/EXIT
6. State counters increment correctly across multiple ticks
7. get_state() returns a snapshot, not a live reference

## CONSTRAINTS
- No imports of concrete component classes
- No direct numpy usage (numpy is for the components, not the orchestrator)
- Output valid Python only
