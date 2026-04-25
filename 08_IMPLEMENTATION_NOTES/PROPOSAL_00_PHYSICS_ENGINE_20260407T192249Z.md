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
    def __init__(self, symbol, max_position_usd, risk_pct):
        self.symbol = symbol
        self.max_position_usd = max_position_usd
        self.risk_pct = risk_pct
        
        self.regime_detector = RegimeDetector()
        self.trend_signal_generator = TrendSignalGenerator()
        self.position_sizer = PositionSizer()
        
        self.state = {
            'symbol': symbol,
            'last_regime': None,
            'last_signal': None,
            'last_size': 0.0,
            'timestamp': None
        }
    
    def tick(self, closes, current_price):
        regime = self.regime_detector.detect(closes)
        
        signal = self.trend_signal_generator.generate(regime, closes, current_price)
        
        size = 0.0
        if signal.get('action', '').lower() in ['buy', 'entry', 'long']:
            size = self.position_sizer.calculate(
                self.max_position_usd,
                self.risk_pct,
                current_price
            )
        
        self.state['last_regime'] = regime
        self.state['last_signal'] = signal
        self.state['last_size'] = size
        self.state['timestamp'] = datetime.now(timezone.utc).isoformat()
        
        return {
            'regime': regime,
            'signal': signal,
            'size': size
        }
    
    def get_state(self):
        return self.state.copy()
```