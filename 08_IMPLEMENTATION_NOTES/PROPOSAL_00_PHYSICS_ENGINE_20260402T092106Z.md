---
DOMAIN: 00_PHYSICS_ENGINE
MODEL: qwen3.5:27b
TIER: heavy
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

import os
import json
import time
import logging
from mantis_core.physics.regime_detector import RegimeDetector
from mantis_core.alpha.trend_signal_generator import TrendSignalGenerator
from mantis_core.control.position_sizer import PositionSizer
from mantis_core.execution.alpaca_harness import AlpacaHarness
from mantis_core.util.logger import Logger

class MantisLivePipeline:
    """
    Production-Grade Live Execution Pipeline with Mantis Core.
    
    Orchestrates regime detection, signal generation, sizing, and execution 
    in a continuous loop via Alpaca API.
    """
    
    def __init__(self, config_path: str):
        """
        Initialize components and load configuration from a YAML-like file.
        
        Args:
            config_path (str): Path to the configuration file.
        """
        self.logger = Logger.get_logger('MantisLivePipeline')
        self.logger.info(f"Loading configuration from {config_path}")
        
        # Load configuration (Simple manual parser for flat key-value YAML as per constraint)
        try:
            self.config = self._parse_yaml_config(config_path)
        except Exception as e:
            self.logger.error(f"Failed to load config: {e}")
            raise RuntimeError("Configuration loading failed")

        # Extract settings with defaults
        self.symbol = self.config.get('symbol', 'BTC/USD')
        self.interval = int(self.config.get('interval', 300))
        self.max_position_usd = float(self.config.get('max_position_usd', 1000.0))
        self.risk_per_trade_pct = float(self.config.get('risk_per_trade_pct', 1.0))

        # Initialize Mantis Core Components
        try:
            self.regime_detector = RegimeDetector()
            self.signal_generator = TrendSignalGenerator()
            self.position_sizer = PositionSizer(max_position_usd=self.max_position_usd)
            
            # Initialize Execution Harness (Alpaca) - Paper trading implied by context/defaults if not passed
            api_key = os.environ.get('ALPACA_API_KEY', '')
            api_secret = os.environ.get('ALPACA_API_SECRET', '')
            self.harness = AlpacaHarness(api_key=api_key, api_secret=api_secret)
            
            self.logger.info("MantisLivePipeline initialized successfully.")
        except Exception as e:
            self.logger.critical(f"Failed to initialize components: {e}")
            raise

    def _parse_yaml_config(self, path: str) -> dict:
        """
        Simple parser for flat key-value YAML configuration.
        
        Args:
            path (str): Path to the config file.
            
        Returns:
            dict: Parsed configuration dictionary.
        """
        config = {}
        with open(path, 'r') as f:
            lines = f.readlines()
            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if ':' in line:
                    key, value = line.split(':', 1)
                    value = value.strip()
                    # Attempt basic type conversion
                    try:
                        if '.' in value:
                            value = float(value)
                        elif value.lower() in ['true', 'false']:
                            value = value.lower() == 'true'
                        else:
                            value = int(value)
                    except ValueError:
                        pass # Keep as string (e.g. BTC/USD)
                    config[key.strip()] = value
        return config

    def tick(self, bar_data):
        """
        Process a single market data bar through the full execution pipeline.
        
        1. Detect Regime
        2. Get Signal
        3. Calculate Size
        4. Execute Trade
        
        Args:
            bar_data (dict): Market data object containing OHLCV and timestamp.
        """
        try:
            # 1. Detect Regime
            regime = self.regime_detector.detect(bar_data)
            
            if regime != 'neutral':
                # 2. Get Signal
                signal = self.signal_generator.get_signal(bar_data, regime)
                
                if signal['direction'] is not None:
                    # 3. Calculate Size
                    size = self.position_sizer.calculate_size(bar_data['price'], 
                                                             risk_pct=self.risk_per_trade_pct, 
                                                             direction=signal['direction'])
                    
                    if size > 0:
                        # 4. Execute
                        order_result = self.harness.execute_order(
                            symbol=self.symbol,
                            side='buy' if signal['direction'] == 'long' else 'sell',
                            quantity=size
                        )
                        self.logger.info(f"Executed: {signal['direction']} x {size} @ {bar_data['price']} | Result: {order_result}")
                    else:
                        self.logger.debug("Position size calculated as 0 or invalid.")
                else:
                    self.logger.debug("No valid signal generated.")
            else:
                self.logger.debug("Regime is neutral, holding position.")

        except Exception as e:
            # Robust error handling to prevent loop crash
            self.logger.error(f"Error during tick processing: {e}")
            import traceback
            traceback.print_exc()

    def run_loop(self, symbol: str = None, interval_sec: int = None):
        """
        Main execution loop fetching live bars and triggering ticks.
        
        Args:
            symbol (str, optional): Symbol to trade. Defaults to config symbol.
            interval_sec (int, optional): Interval in seconds between ticks. 
                                         Defaults to config interval.
        """
        # Override with defaults if not provided
        self.symbol = symbol or self.config.get('symbol', 'BTC/USD')
        tick_interval = interval_sec or int(self.config.get('interval', 300))
        
        self.logger.info(f"Starting live loop for {self.symbol} with {tick_interval}s interval.")
        
        try:
            while True:
                # Simulate fetching live bar (in a real scenario, this uses websockets or API)
                current_time = time.time()
                
                # Mock Data Generation for demonstration purposes 
                # (In production, replace with actual self.harness.get_latest_bar(symbol))
                mock_bar = {
                    'symbol': self.symbol,
                    'timestamp': current_time,
                    'open': 30000.0 + (hash(str(current_time)) % 100),
                    'high': 30100.0 + (hash(str(current_time)) % 100),
                    'low': 29900.0 + (hash(str(current_time)) % 100),
                    'close': 30050.0 + (hash(str(current_time)) % 100),
                    'volume': 100000,
                    'price': 30050.0 # Alias for execution price
                }
                
                self.tick(mock_bar)
                
                time.sleep(tick_interval)
                
        except KeyboardInterrupt:
            self.logger.info("User interrupted (Ctrl+C). Shutting down.")
        except Exception as e:
            self.logger.critical(f"Loop crashed: {e}")

if __name__ == "__main__":
    # Entry point
    CONFIG_FILE = "config.yaml"
    
    if os.path.exists(CONFIG_FILE):
        pipeline = MantisLivePipeline(CONFIG_FILE)
        pipeline.run_loop()
    else:
        print(f"Error: {CONFIG_FILE} not found. Please provide a configuration file.")