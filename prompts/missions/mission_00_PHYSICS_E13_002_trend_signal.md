# MISSION: Trend Signal Generator
DOMAIN: 00_PHYSICS_ENGINE
TASK: 00_PHYSICS_E13_002_trend_signal
TYPE: IMPLEMENTATION
VERSION: 1.0

## CONTEXT
The trend signal generator consumes regime classifications and price data
to produce actionable entry/exit signals. It only generates signals in
TRENDING_UP or TRENDING_DOWN regimes; in RANGING or VOLATILE regimes it
returns NO_ACTION to keep MANTIS out of choppy markets.

The previous E11 attempt produced a 12-line stub that didn't actually
compute signals. This mission builds the real version.

## EXACT IMPORTS:
```python
import numpy as np
from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional
```

## INTERFACE CONTRACT
The deliverable is `mantis_core/physics/trend_signal.py` containing:

### Enum: SignalAction
Four possible actions:
- ENTER_LONG
- ENTER_SHORT
- EXIT
- NO_ACTION

### Dataclass: TradeSignal
Frozen dataclass with these exact fields:
```
action: SignalAction
strength: float            # 0.0 to 1.0
entry_price: Optional[float]
stop_loss: Optional[float]
take_profit: Optional[float]
reasoning: str             # short human-readable explanation
timestamp: datetime        # UTC
```

### Class: TrendSignalGenerator
Constructor accepts these parameters with defaults:
- ema_fast_period: int = 20
- ema_slow_period: int = 50
- atr_stop_multiplier: float = 2.0
- atr_target_multiplier: float = 3.0

Method: `generate_signal(self, closes: np.ndarray, current_price: float, regime: str, atr: float) -> TradeSignal`

The method must:
1. Accept a numpy array of closes, current price, regime string, and current ATR
2. Raise ValueError if closes has fewer than ema_slow_period elements
3. Compute fast and slow EMAs
4. Return TradeSignal with NO_ACTION if regime is "RANGING", "VOLATILE", or "UNKNOWN"
5. For TRENDING_UP regime: return ENTER_LONG when fast EMA > slow EMA AND current_price > fast EMA
6. For TRENDING_DOWN regime: return ENTER_SHORT when fast EMA < slow EMA AND current_price < fast EMA
7. Compute stop_loss as current_price -/+ (atr * atr_stop_multiplier) based on direction
8. Compute take_profit as current_price +/- (atr * atr_target_multiplier) based on direction
9. Strength scales with |fast EMA - slow EMA| / current_price, clamped to [0, 1]

## DELIVERABLE
File: mantis_core/physics/trend_signal.py

## BEHAVIORAL REQUIREMENTS
- Deterministic: same input always produces same output
- Pure numpy: no pandas, no talib
- No file I/O, no network calls, no global state
- All prices must be positive floats; raise ValueError on invalid
- Signal strength must be in [0.0, 1.0]
- Stops and targets must be on the correct side of entry price

## TEST REQUIREMENTS
The corresponding test mission will verify:
1. generate_signal raises ValueError for short close arrays
2. Returns NO_ACTION for RANGING, VOLATILE, UNKNOWN regimes
3. Returns ENTER_LONG when TRENDING_UP and EMAs cross up
4. Returns ENTER_SHORT when TRENDING_DOWN and EMAs cross down
5. Stop loss is below entry for long, above entry for short
6. Take profit is above entry for long, below entry for short
7. Signal strength always in [0.0, 1.0]
8. Same input produces same output (deterministic)

## CONSTRAINTS
- numpy only
- No talib, no pandas
- Output valid Python only
