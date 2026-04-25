# MISSION: BTC/USD Regime Detector
DOMAIN: 00_PHYSICS_ENGINE
TASK: 00_PHYSICS_E13_001_regime_detector
TYPE: IMPLEMENTATION
VERSION: 1.0

## CONTEXT
MANTIS targets BTC/USD with regime-aware execution. Before any signal
generation, the system must classify the current market regime from raw
OHLC data. This module is the foundation of the trading pipeline.

The previous E11 attempt produced 290 lines of indicator math but used
the wrong class name and method signature. This mission builds the proper
version with a clear interface contract.

## EXACT IMPORTS:
```python
import numpy as np
from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional
```

## INTERFACE CONTRACT
The deliverable is `mantis_core/physics/regime_detector.py` containing:

### Enum: Regime
Four regime states plus an unknown fallback:
- TRENDING_UP
- TRENDING_DOWN
- RANGING
- VOLATILE
- UNKNOWN

### Dataclass: RegimeState
Frozen dataclass with these exact fields:
```
regime: Regime
confidence: float          # 0.0 to 1.0
adx: float                 # current ADX value
atr: float                 # current ATR value
atr_ratio: float           # current ATR / 50-bar ATR average
timestamp: datetime        # UTC
```

### Class: RegimeDetector
Constructor takes no arguments. State is held internally per call.

Method: `classify_regime(self, closes: np.ndarray, highs: np.ndarray, lows: np.ndarray) -> RegimeState`

The method must:
1. Accept three numpy float arrays of equal length
2. Raise ValueError if any array has fewer than 60 elements
3. Raise ValueError if the arrays have unequal lengths
4. Compute ADX, +DI, -DI using Wilder smoothing with period=14
5. Compute ATR with period=14
6. Compute 50-bar EMA of close
7. Compute Bollinger Band width with period=20
8. Apply this classification logic in priority order:
   - VOLATILE if current ATR > 2.0 * 50-bar ATR average
   - RANGING if ADX < 20 AND Bollinger width is contracting
   - TRENDING_UP if ADX >= 25 AND close > EMA50 AND +DI > -DI
   - TRENDING_DOWN if ADX >= 25 AND close < EMA50 AND -DI > +DI
   - UNKNOWN otherwise
9. Return a RegimeState with all fields populated

## DELIVERABLE
File: mantis_core/physics/regime_detector.py

## BEHAVIORAL REQUIREMENTS
- Deterministic: same input always produces same output
- Pure numpy: no pandas, no talib, no external indicator libraries
- All indicator math computed from raw arrays
- No file I/O, no network calls, no global state
- Confidence score must be in [0.0, 1.0]
- Timestamps must be timezone-aware (UTC)

## TEST REQUIREMENTS
The corresponding test mission will verify:
1. classify_regime raises ValueError for arrays shorter than 60 elements
2. classify_regime raises ValueError for unequal array lengths
3. Returns RegimeState dataclass with all fields populated
4. Synthetic trending-up data classified as TRENDING_UP
5. Synthetic flat data classified as RANGING
6. Synthetic high-volatility data classified as VOLATILE
7. Confidence scores always in [0.0, 1.0]
8. Same input produces same output across calls (deterministic)

## CONSTRAINTS
- numpy only
- No talib, no pandas
- All indicator math from scratch with explicit formulas
- Output valid Python only
