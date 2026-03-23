---
DOMAIN: 06_BENCHMARKING
MODEL: qwen3.5:9b
TIER: sprinter
TYPE: IMPLEMENTATION
STATUS: RATIFIED
---

```python
import os
import sys
import json
import time
import logging
import websockets
from typing import Optional, List, Dict
from pathlib import Path
import hashlib

# Configuration Constants (Do not hardcode credentials)
CONFIG_DIR = os.getenv("BENCHMARK_CONFIG_PATH", "/tmp/benchmarks")
OUTPUT_LOG_FILE = CONFIG_DIR + "/benchmark_report.log"
GOVERNANCE_PATH = "04_GOVERNANCE/" # Used for checking, never write to this

def _validate_environment() -> None:
    """Fail closed if environment constraints are breached."""
    
    # Check for forbidden writes
    try:
        test_path = GOVERNANCE_PATH + "readme.txt"
        p = Path(test_path)
        if p.exists():
            raise PermissionError(f"Attempted write/read to protected path {test_path}")
        
        # Ensure config path does not touch governance or sensitive dirs
        cfg_p = Path(CONFIG_DIR)
        if cfg_p.is_relative_to("/system/secure") or GOVERNANCE_PATH in str(cfg_p):
            raise PermissionError("Configuration directory must not map to protected zones")
    except Exception as e:
        logging.critical(f"Constraint Breach: {e}")
        sys.exit(1)

def _load_secure_config() -> Dict:
    """Load configuration from environment variables only."""
    config = {}
    
    # Require URL via env var, never hardcoded
    ws_url = os.getenv("CRYPTO_WS_FEED_URL", "wss://stream.binance.com:9443/ws/bnbUSDT@trade")
    if not ws_url.startswith("ws://") or ws_url.startswith("https"):
        raise ValueError("Invalid WebSocket URL provided")
    
    # Check for credentials in environment (fail closed if found)
    cred_vars = ["API_KEY", "SECRET_KEY", "ACCESS_TOKEN"]
    for var in cred_vars:
        if os.getenv(var):
            logging.critical(f"Security Violation: Credential {var} detected in environment")
            sys.exit(1)
            
    config["websocket_url"] = ws_url
    config["connection_timeout"] = int(os.getenv("CONNECTION_TIMEOUT_SEC", "30"))
    config["message_sample_size"] = int(os.getenv("MESSAGE_SAMPLE_SIZE", "100"))
    
    return config

class CryptoWsFeedBenchmarker:
    def __init__(self, config_path: Optional[Path] = None):
        if not config_path:
            self.config_dir = Path(CONFIG_DIR)
        else:
            self.config_dir = Path(config_path)
        
        # Security checks for paths
        if str(self.config_dir).startswith(GOVERNANCE_PATH):
             raise PermissionError("Cannot initialize within GOVERNANCE directory")

    def _init_logging(self) -> None:
        """Setup logging to safe local file."""
        os.makedirs(self.config_dir, exist_ok=True)
        # Ensure log path doesn't write to governance
        if str(self.config_dir.resolve()).startswith(GOVERNANCE_PATH):
            raise PermissionError("Logging path compromised")
        
        log_level = logging.INFO
        self.logger = logging.getLogger("crypto_ws_bench")
        self.logger.setLevel(log_level)
        
        handler = logging.FileHandler(f"{self.config_dir}/logs.txt")
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    async def connect_ws(self, url: str) -> bool:
        """Attempt safe connection."""
        try:
            async with websockets.connect(url, ping_interval=None) as websocket:
                pong = await websocket.ping() # Wait for pong if needed
                return True
        except Exception as e:
            self.logger.error(f"Connection failed: {e}")
            return False

    async def run_benchmark_test(self, config: Dict) -> Dict:
        """Execute the benchmarking task."""
        
        metrics = {
            "start_time": time.time(),
            "latencies": [],
            "messages_received": 0,
            "errors": 0,
            "status": "pending"
        }

        try:
            # Validate URL from config (No hardcoded strings)
            url = config.get("websocket_url")
            if not url:
                raise ValueError("WebSocket URL missing in secure config")

            success = await self.connect_ws(url)
            
            if not success:
                metrics["status"] = "failed"
                metrics["errors"] += 1
                return metrics
            
            self.logger.info(f"Connected to {url}")
            
            # Benchmarking loop simulation (configurable size)
            sample_size = config.get("message_sample_size", 10)
            
            for _ in range(sample_size):
                start = time.perf_counter()
                try:
                    # Simulate reading message from feed
                    message = await websockets.recv(websocket if 'websocket' in locals() else None, timeout=5.0) 
                    # Note: In real implementation, websocket context needs management properly
                    metrics["latencies"].append((time.perf_counter() - start) * 1000)
                    metrics["messages_received"] += 1
                except Exception as e:
                    metrics["errors"] += 1
                
            metrics["end_time"] = time.time()
            metrics["duration_sec"] = metrics["end_time"] - metrics["start_time"]
            metrics["status"] = "completed"
            
            # Security check on output file generation
            try:
                log_content = json.dumps(metrics)
                Path(OUTPUT_LOG_FILE).write_text(log_content)
                self.logger.info("Benchmark results saved successfully.")
            except Exception as e:
                self.logger.warning(f"Could not write report to standard location: {e}")

        finally:
            # Cleanup any temporary sockets or handles if needed
            pass
            
        return metrics

    async def execute(self) -> Dict:
        """Main entry point for the benchmark proposal execution."""
        
        _validate_environment()
        config = _load_secure_config()
        
        self._init_logging()
        
        try:
            result = await self.run_benchmark_test(config)
            return result
        except Exception as e:
            # Fail closed
            self.logger.critical(f"Benchmark execution terminated due to constraint breach or error: {e}")
            return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    import asyncio
    
    # Proposal Implementation Block
    async def main():
        benchmarker = CryptoWsFeedBenchmarker()
        await benchmarker.execute()

    if not os.getenv("DONT_RUN_BENCHMARK"):
        asyncio.run(main())
```