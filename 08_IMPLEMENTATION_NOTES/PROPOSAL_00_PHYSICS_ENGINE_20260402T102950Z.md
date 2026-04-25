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
import yaml
from mantis_core.physics.regime_detector import RegimeDetector
from mantis_core.physics.trend_signal import TrendSignalGenerator
from mantis_core.physics.alpaca_harness import AlpacaHarness
from mantis_core.risk.position_sizer import PositionSizer


class MantisLivePipeline:
    def __init__(self, config_path):
        """Initialize pipeline with config file and all 4 modules."""
        self.config = self._load_config(config_path)
        self.logger = logging.getLogger(__name__)
        
        # Initialize all 4 modules
        self.regime_detector = RegimeDetector()
        self.signal_generator = TrendSignalGenerator()
        self.position_sizer = PositionSizer(
            max_position_usd=self.config.get('max_position_usd', 1000),
            risk_per_trade_pct=self.config.get('risk_per_trade_pct', 1.0)
        )
        
        # Alpaca harness with env-based credentials (paper trading ONLY)
        api_key = os.environ.get('ALPACA_API_KEY')
        secret_key = os.environ.get('ALPACA_SECRET_KEY')
        self.alpaca_harness = AlpacaHarness(api_key=api_key, secret_key=secret_key)
        
        self.state = {
            'initialized': True,
            'last_regime': None,
            'last_signal': None,
            'last_size': None,
            'last_order': None,
            'tick_count': 0,
            'errors': []
        }
    
    def _load_config(self, config_path):
        """Load configuration from YAML file."""
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        
        with open(path, 'r') as f:
            return yaml.safe_load(f)
    
    def tick(self, bar_data):
        """Process single bar update cycle."""
        try:
            self.state['tick_count'] += 1
            
            # Feed bar to RegimeDetector -> get regime
            regime = self.regime_detector.analyze(bar_data)
            self.state['last_regime'] = regime
            
            # Feed bar + regime to TrendSignalGenerator -> get signal
            signal = self.signal_generator.generate(bar_data, regime)
            self.state['last_signal'] = signal
            
            result = {'status': 'processed', 'tick_count': self.state['tick_count']}
            
            # If signal has entry: PositionSizer -> calculate size
            if signal.get('entry') or signal.get('action'):
                size = self.position_sizer.calculate(
                    symbol=self.config.get('symbol'),
                    price=bar_data.get('close', bar_data.get('price')),
                    signal_strength=signal.get('strength', 1.0)
                )
                self.state['last_size'] = size
                
                # If sized: AlpacaHarness -> submit paper order
                if size and size.get('quantity', 0) > 0:
                    try:
                        order = self.alpaca_harness.submit_paper_order(
                            symbol=self.config.get('symbol'),
                            quantity=size['quantity'],
                            side=signal.get('side', 'buy'),
                            price=bar_data.get('close')
                        )
                        self.state['last_order'] = order
                        result['status'] = 'order_submitted'
                        result['order'] = order
                    except Exception as e:
                        error_msg = f"Alpaca unreachable: {str(e)}"
                        self.logger.warning(error_msg)
                        self.state['errors'].append({'type': 'alpaca', 'error': error_msg})
                        result['status'] = 'alpaca_error'
                        result['error'] = error_msg
                else:
                    result['status'] = 'no_size_calculated'
            else:
                result['status'] = 'no_signal_entry'
            
            return result
        
        except Exception as e:
            error_msg = f"Tick error: {str(e)}"
            self.logger.error(error_msg)
            self.state['errors'].append({'type': 'tick', 'error': error_msg})
            return {'status': 'error', 'error': error_msg, 'tick_count': self.state['tick_count']}
    
    def run_loop(self, symbol=None, interval_sec=5):
        """Poll Alpaca for latest bar and call tick()."""
        if symbol is None:
            symbol = self.config.get('symbol')
        
        if interval_sec <= 0:
            raise ValueError("interval_sec must be positive")
        
        self.logger.info(f"Starting pipeline loop for {symbol} at {interval_sec}s intervals")
        
        try:
            while True:
                try:
                    # Poll Alpaca for latest bar
                    bar_data = self.alpaca_harness.get_latest_bar(symbol)
                    
                    if bar_data:
                        result = self.tick(bar_data)
                        self.logger.info(f"Tick {self.state['tick_count']}: {result['status']}")
                    else:
                        self.logger.debug("No bar data received, waiting...")
                    
                    time.sleep(interval_sec)
                
                except Exception as e:
                    error_msg = f"Run loop poll error: {str(e)}"
                    self.logger.error(error_msg)
                    self.state['errors'].append({'type': 'loop', 'error': error_msg})
                    # Graceful degradation - wait and retry
                    time.sleep(min(interval_sec * 2, 30))
        
        except KeyboardInterrupt:
            self.logger.info("Pipeline stopped by user")
    
    def get_state(self):
        """Return JSON-serializable pipeline state."""
        return {
            'config': {
                'symbol': self.config.get('symbol'),
                'interval': self.config.get('interval'),
                'max_position_usd': self.config.get('max_position_usd'),
                'risk_per_trade_pct': self.config.get('risk_per_trade_pct')
            },
            'state': {
                'initialized': self.state['initialized'],
                'last_regime': self.state['last_regime'],
                'last_signal': self.state['last_signal'],
                'last_size': self.state['last_size'],
                'last_order': self.state['last_order'],
                'tick_count': self.state['tick_count'],
                'error_count': len(self.state['errors']),
                'recent_errors': self.state['errors'][-10:]
            },
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
```