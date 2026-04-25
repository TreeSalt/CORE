---
DOMAIN: 00_PHYSICS_ENGINE
MODEL: qwen3.5:27b
TIER: heavy
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

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


class MantisLivePipeline:
    def __init__(self, symbol="BTC/USD", max_position_usd=1000, risk_pct=1.0):
        self.symbol = symbol
        self.max_position_usd = max_position_usd
        self.risk_pct = risk_pct
        self.regime_detector = RegimeDetector()
        self.signal_gen = TrendSignalGenerator()
        self.sizer = PositionSizer()
        self.state = {"trades": 0, "regime": "unknown", "last_signal": None}

    def tick(self, bar):
        """Process one bar: detect regime, generate signal, size position."""
        # 1. Update regime detector with bar
        closes = bar.get("closes", [])
        if len(closes) >= 10:
            closes_array = np.array(closes[-10:])
            regime = self.regime_detector.detect(closes_array)
        else:
            regime = "unknown"
        
        # 2. Get signal from trend signal generator
        signal_dict = self.signal_gen.generate(bar, regime)
        
        # 3. If signal is entry: calculate position size
        position_size = None
        if signal_dict.get("action") == "entry":
            equity = bar.get("equity", self.max_position_usd)
            entry_price = bar.get("close", bar.get("last", 0))
            stop_loss = signal_dict.get("stop_loss", entry_price * 0.98)
            
            position_size = self.sizer.calculate(
                equity=equity,
                risk_pct=self.risk_pct,
                entry=entry_price,
                stop_loss=stop_loss
            )
            
            # Cap position size at max_position_usd
            if position_size is not None and position_size > self.max_position_usd:
                position_size = self.max_position_usd
        
        # 4. Update self.state
        self.state["regime"] = regime
        self.state["last_signal"] = signal_dict.get("action", "none")
        if position_size is not None and position_size > 0:
            self.state["trades"] += 1
        
        # 5. Return dict with regime, signal, size (or None)
        return {
            "regime": regime,
            "signal": signal_dict.get("action", "none"),
            "size": position_size
        }

    def get_state(self):
        return self.state.copy()
```