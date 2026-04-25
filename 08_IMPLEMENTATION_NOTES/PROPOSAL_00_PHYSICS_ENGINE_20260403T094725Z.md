---
DOMAIN: 00_PHYSICS_ENGINE
MODEL: qwen3.5:27b
TIER: heavy
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

import os
import json
import logging
import time
import copy
from mantis_core.physics.regime_detector import RegimeDetector
from mantis_core.physics.trend_signal import TrendSignalGenerator
from mantis_core.risk.position_sizer import PositionSizer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MantisLivePipeline:
    def __init__(self):
        # Implementation omitted for brevity
        self.regime_detector = RegimeDetector()
        self.signal_gen = TrendSignalGenerator()
        self.sizer = PositionSizer()
        
        # Initial state configuration
        self.state = {
            'regime': None,
            'last_signal': None,
            'current_size': 0.0,
            'trades': []
        }

    def tick(self, bar):
        """Process a new market bar and update the state."""
        try:
            # Step 1: Update Regime Detector with bar data
            # The hint suggests passing numpy arrays of closes; assuming bar provides necessary context.
            regime = self.regime_detector.update(bar)
            
            # Step 2: Generate trend signal based on bar and detected regime
            signal = self.signal_gen.generate(bar, regime)
            
            # Step 3: Determine position size based on signal strength and risk parameters
            size = self.sizer.calculate(signal) if signal else 0.0
            
            # Update internal state dictionary
            self.state['regime'] = regime
            self.state['last_signal'] = signal
            self.state['current_size'] = size
            
            # Log trades or state changes for monitoring
            if signal:
                trade_record = {
                    'timestamp': time.time(),
                    'signal_strength': signal.get('strength', 0.0),
                    'size': size,
                    'regime': regime
                }
                self.state['trades'].append(trade_record)
                
            # Optional: Periodically cleanup trade history to prevent memory bloat
            if len(self.state['trades']) > 1000:
                self.state['trades'] = self.state['trades'][-500:]

        except Exception as e:
            logger.error(f"Pipeline error in tick loop: {str(e)}")
            raise

    def get_state(self):
        """Return a deep copy of self.state."""
        return copy.deepcopy(self.state)