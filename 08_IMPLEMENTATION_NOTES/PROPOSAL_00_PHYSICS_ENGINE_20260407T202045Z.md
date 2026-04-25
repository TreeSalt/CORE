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
from datetime import datetime, timezone
from pathlib import Path
from mantis_core.physics.regime_detector import RegimeDetector
from mantis_core.physics.trend_signal import TrendSignalGenerator
from mantis_core.risk.position_sizer import PositionSizer

logger = logging.getLogger(__name__)


class MantisLivePipeline:
    def __init__(self, symbol, max_position_usd, risk_pct):
        self.symbol = symbol
        self.max_position_usd = float(max_position_usd)
        self.risk_pct = float(risk_pct)
        
        # Ensure credentials are fetched from environment if required by components
        api_key = os.environ.get("MANTIS_API_KEY")
        secret_key = os.environ.get("MANTIS_SECRET_KEY")
        
        # Initialize core physics and risk components
        try:
            self.regime_detector = RegimeDetector()
            self.signal_generator = TrendSignalGenerator()
            self.position_sizer = PositionSizer(max_position_usd=self.max_position_usd, risk_pct=self.risk_pct)
        except Exception as e:
            logger.critical(f"Failed to initialize pipeline components: {e}")
            raise

        # Initialize internal state
        self.state = {
            'last_regime': None,
            'last_signal': None,
            'calculated_size': 0.0,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }

    def tick(self, closes, current_price):
        """
        Processes a single tick/update of market data.
        
        Args:
            closes (numpy.ndarray or list): Historical closing prices.
            current_price (float): The current price for sizing/signal validation.
            
        Returns:
            dict: Execution decision containing regime, signal, and size.
        """
        try:
            # 1. Regime Detection
            # Call RegimeDetector to classify the current market regime based on closes
            regime = self.regime_detector.detect(closes)
            if not regime:
                logger.warning("Regime detector returned None or invalid value.")
                return {
                    'regime': None,
                    'signal': 'HOLD',
                    'size': 0.0
                }

            # 2. Signal Generation
            # Pass the regime and price data to TrendSignalGenerator for a signal
            signal = self.signal_generator.generate(regime, closes, current_price)

            # 3. Position Sizing
            # If the signal suggests an entry, call PositionSizer to compute position size
            calculated_size = 0.0
            
            # Interpret signal: Assuming 'ENTRY' or non-zero numeric value triggers sizing
            is_entry_signal = (signal == 'ENTRY') or \
                              (isinstance(signal, (int, float)) and signal > 0)

            if is_entry_signal:
                try:
                    calculated_size = self.position_sizer.size(current_price)
                except Exception as size_err:
                    logger.error(f"Sizing calculation failed: {size_err}")
                    calculated_size = 0.0
            
            # 4. State Update
            self.state['last_regime'] = regime
            self.state['last_signal'] = signal
            self.state['calculated_size'] = calculated_size
            self.state['timestamp'] = datetime.now(timezone.utc).isoformat()

            return {
                'regime': regime,
                'signal': signal,
                'size': calculated_size
            }

        except Exception as e:
            logger.error(f"Critical error in tick processing for {self.symbol}: {e}")
            return {
                'regime': self.state.get('last_regime'),
                'signal': 'ERROR',
                'size': 0.0
            }

    def get_state(self):
        """Returns a copy of the current pipeline state."""
        return self.state.copy()