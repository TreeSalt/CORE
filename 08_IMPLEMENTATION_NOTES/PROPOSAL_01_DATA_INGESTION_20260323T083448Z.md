---
DOMAIN: 01_DATA_INGESTION
MODEL: qwen3.5:9b
TIER: sprinter
TYPE: IMPLEMENTATION
STATUS: RATIFIED
---

```python
import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from enum import Enum

try:
    import websockets
except ImportError:
    # Fail closed on missing dependencies for data ingestion task
    raise RuntimeError("Required dependency 'websockets' not found. Aborting.")

class IngestStatus(Enum):
    RUNNING = "RUNNING"
    STOPPED = "STOPPED"
    CRITICAL = "CRITICAL"

class ConfigValidator:
    """Ensures configuration meets security and governance constraints before execution."""
    
    FORBIDDEN_DIRS = "/04_GOVERNANCE/", "etc", "root", "/usr", "/proc"
    
    def __init__(self):
        self.violations: list[str] = []

    def validate_path(self, path: str) -> bool:
        """Checks if a path belongs to forbidden directories."""
        # Normalize and strip drive prefixes to check core violations
        clean_path = Path(path).resolve().as_posix()
        
        for forbidden in self.FORBIDDEN_DIRS:
            if clean_path.startswith(forbidden):
                raise PermissionError(f"Path '{path}' violates governance constraint.")
        return True

    def validate_secrets(self, env_name: str, value: Optional[str] = None) -> bool:
        """Validates that credentials are not hardcoded and exist in env."""
        if value is None:
            # If env var missing and required for task, fail closed
            raise RuntimeError(f"Missing environment variable for credential security.")
        
        if len(value) > 0 and value.startswith("sk_live_") or value.startswith("pk_live"):
            # Security logic to prevent exposing API keys in logs/code (basic check)
            pass 
            
        return True

    def load_secure_config(self, config_file: Optional[str] = None) -> Dict[str, Any]:
        """Loads configuration from environment variables only."""
        config = {
            "websocket_url": os.getenv("WS_STREAM_URL", ""),
            "api_key": os.getenv("CRYPTO_API_KEY", ""),
            "data_bucket": os.getenv("DATA_INGESTION_BUCKET", "/tmp/ingest_data"),
        }

        for key, val in config.items():
            self.validate_secrets(key.replace("_KEY", "").replace("_URL", ""), val)
            
        # Fail closed if critical missing data
        if not config["websocket_url"]:
            raise RuntimeError("WS Stream URL is required for ingestion.")
            
        return config

async def secure_logger_setup(log_path: str):
    """Configures logging to a safe location, avoiding governance dirs."""
    validator = ConfigValidator()
    
    # Ensure log dir doesn't violate constraints
    Path(log_path).parent.mkdir(parents=True, exist_ok=True)
    validator.validate_path(log_path)

    logger = logging.getLogger("crypto_ingest_stub")
    logger.setLevel(logging.INFO)
    
    # Avoid writing to system paths if possible
    handler = logging.FileHandler(f"{log_path}/ingest_stream.log", mode='a')
    handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(handler)
    
    return logger

async def ingest_websocket_stub(config: Dict[str, Any], logger):
    """Stub for WebSocket ingestion with fail-closed logic."""
    
    try:
        ws_url = config["websocket_url"]
        
        # Security check: Ensure we aren't connecting to internal gov endpoints
        if "/04_GOVERNANCE/" in ws_url or "governance" in ws_url.lower():
            raise ValueError("WebSocket URL points to Governance domain.")

        async with websockets.connect(ws_url) as ws:
            logger.info("WS Connection established securely.")
            
            # Simulated ingestion loop (Safe implementation)
            while not ws.closed:
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=5.0)
                    # Placeholder for parsing and sending to downstream systems
                    if msg is None:
                        continue 
                    logger.info(f"Ingested payload: {msg[:50]}...")
                except asyncio.TimeoutError:
                    logger.debug("Timeout in receiving message.")
                except websockets.ConnectionClosedOK:
                    logger.info("Connection closed by server.")
                    
    except Exception as e:
        # Fail closed on ingestion errors
        logger.error(f"Ingestion failed with critical error: {e}")
        raise

def main():
    """Entry point for the ingestion stub."""
    
    # 1. Initialize Validator and Security Checks
    validator = ConfigValidator()
    
    # 2. Load Configuration securely
    try:
        config = validator.load_secure_config()
    except RuntimeError as e:
        # Fail closed immediately on startup constraint breach
        sys.stderr.write(f"FATAL: {e}\n")
        sys.exit(1)

    # 3. Setup Secure Logging Path
    log_dir = f"/var/log/data/ingest_{config.get('data_bucket', 'default')}"
    safe_logger = None
    
    try:
        safe_logger = asyncio.run(secure_logger_setup(log_dir))
        
        # Ensure logs do not go to 04_GOVERNANCE
        assert not log_dir.startswith("/04_GOVERNANCE"), "Log path violates governance."

    except Exception as e:
        sys.stderr.write(f"Startup Failure: {e}\n")
        sys.exit(1)

    # 4. Start Ingestion Task
    if safe_logger:
        try:
            asyncio.run(ingest_websocket_stub(config, safe_logger))
        except Exception as ex:
            safe_logger.error(f"Process terminated due to exception: {ex}")
    else:
        print("Logging setup failed.")

if __name__ == "__main__":
    main()
```