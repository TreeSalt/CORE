---
DOMAIN: 00_PHYSICS_ENGINE
MODEL: qwen3.5:9b
TIER: cruiser
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

```python
import time
from datetime import datetime, timedelta
import json
import os
import logging
import yaml
import pathlib
from mantis_core.physics.utils.RiskManager as RiskManager
from mantis_core.core.strategy_components.AlpacaHarness as AlpacaHarness
from mantis_core.core.signal_generators.TrendSignalGenerator as TrendSignalGenerator
from mantis_core.core.regime_detectors.RegimeDetector as RegimeDetector

class AlpacaStrategy:
    def __init__(self, config_path: str):
        # Load configuration from YAML file
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        self.logger = logging.getLogger(__name__)
        
        # Extract configuration values
        self.symbol = config.get('symbol', config['default_symbol']) if isinstance(config, dict) else config.get('symbol')
        self.interval_sec = config.get('interval_seconds', 60)
        
        # Risk Management setup
        # Use RiskManager to set position size based on risk settings from config or environment variables
        
        # Retrieve API keys from environment for Alpaca Harness (secure practice)
        self.api_key = os.getenv("ALPACA_API_KEY")
        self.api_secret = os.getenv("ALPACA_API_SECRET")
        self.maintenance_tenant = os.getenv("ALPACA_MAINTENANCE_TENANT", "") # Usually default is "" for non-maintenance tenant
        
        # Risk settings from config (or fallback defaults)
        max_position_usd = float(config.get('risk_per_trade_usd', 500)) # Example default 500 USD
        risk_manager = RiskManager()
        
        # Store AlpacaHarness with initialized API keys
        try:
            self.alpaca_harness = AlpacaHarness(
                api_key=self.api_key,
                api_secret=self.api_secret,
                maintenance_tenant=self.maintenance_tenant
            )
        except Exception as e:
            self.logger.error(f"Error initializing AlpacaHarness: {e}")
            raise
        
        # Initialize signal generators (Trend based)
        try:
            self.trend_generator = TrendSignalGenerator()
        except Exception as e:
            self.logger.error(f"Error initializing TrendSignalGenerator: {e}")
            raise
            
        # Try to detect regime from config or defaults
        try:
            self.regime_detector = RegimeDetector(regime=0) # Default regime (usually 0 or 'normal')
        except Exception as e:
            self.logger.error(f"Error initializing RegimeDetector: {e}")
            raise
            
        # Store last known position size for risk management updates if needed
        self.current_risk = max_position_usd
        self.state = {"position_size": self.current_risk, "last_trade_time": None}

    def run_loop(self):
        """Main polling loop until market is closed or connection fails."""
        while True:
            try:
                # Poll for bar_data update.
                # AlpacaHarness usually provides 'bar_data' which contains the current OHLCV bar.
                self.logger.debug("Checking for new bar data...")
                
                # Wait for bar_data to update or market close check.
                # If connection fails or market is closed, break loop.
                time.sleep(self.interval_sec) 
                
                if not self.alpaca_harness.bar_data:  # Example check for bar_data availability
                    # If no bars are available and we assume market is closed (or data feed error), break.
                    break
                else:
                    # Process new bar data
                    self.tick(self.alpaca_harness.bar_data)
                    
            except Exception as e:
                self.logger.error(f"Unexpected error in loop: {e}")
                break

    def tick(self, bar_data):
        """Execute logic for the latest available bar. 
           If market is closed (detected via lack of data or harness state), stop."""
        if not self.alpaca_harness.bar_data:
            return

        # Calculate position size based on current risk settings
        max_size = RiskManager.calculate_max_size(self.symbol)
        
        # Generate signals from TrendSignalGenerator
        trend_signal = self.trend_generator.get_signal()
        
        # If trade signal present, execute via AlpacaHarness (open/close/modify)
        if trend_signal:
            try:
                # Example: Open position or modify existing one
                # Logic for handling long/short logic would go here.
                pass 
            except Exception as e:
                self.logger.error(f"Error executing trade: {e}")
        else:
            # Close if signal is flat/no longer active
            # Pass to maintain correct state or risk level
            
        # Update state (position, time)
        self.state["last_trade_time"] = datetime.now().isoformat()

    def get_state(self):
        """Return current strategy state (e.g., last trade details)."""
        return self.state

# Example Config YAML format:
# ---
# symbol: AAPL
# interval_seconds: 60
# risk_per_trade_usd: 100.5
# alpaca_maintenance_tenant: "" # Optional if API key provided without maintenance tenant flag
```<|endoftext|><|im_start|>user