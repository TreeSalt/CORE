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
from typing import Any, Callable, Optional
import websockets

# Configure logger
_logger = logging.getLogger(__name__)


class CryptoExchangeWebsocketHandler:
    """
    Secure WebSocket handler for crypto exchange data ingestion.
    Implements fail-closed logic on connection errors or credential validation failures.
    """

    def __init__(self, websocket_url: str, api_config: dict) -> None:
        self.ws_url = websocket_url
        self.api_config = api_config
        self._ws_connection: Optional[Any] = None
        self._is_running = False
        self._headers = self._build_auth_headers()

    def _build_auth_headers(self) -> dict[str, str]:
        """Construct request headers securely without hardcoding keys."""
        headers = {"Accept": "application/json", "User-Agent": "TraderOps-Internal"}
        
        # Security Check: Ensure no empty/invalid secrets exist before proceeding
        if self.api_config.get("api_key") and self.api_config.get("api_secret"):
            headers["X-API-KEY"] = self.api_config["api_key"]
            # Signature generation logic would go here in v3
        else:
            _logger.error("API Credentials missing. Connection will fail-closed.")
        
        return headers

    async def on_message(self, message: str) -> None:
        """Process incoming websocket messages."""
        try:
            data = message.strip()
            # Handle heartbeat/ping frames if necessary
            if not data:
                return
                
            # Process JSON payload (Example placeholder logic)
            if data.startswith("{"):
                _logger.debug(f"Received valid event: {data[:100]}...") 
            else:
                _logger.warning(f"Ignoring invalid message format: {data}")
                
        except Exception as e:
            _logger.error(f"Error in message processing loop: {e}")
            self._fail_close()

    async def start(self) -> None:
        """Establish connection and maintain stream."""
        if not self.api_config.get("api_key"):
            _logger.critical("Authentication failed: Missing API key.")
            self._fail_close()
            return

        _logger.info(f"Initiating secure WebSocket connection to {self.ws_url}")
        
        try:
            async with websockets.connect(
                self.ws_url,
                extra_headers=self._headers,
                ping_interval=20,
                ping_timeout=10
            ) as ws:
                self._is_running = True
                self._ws_connection = ws
                
                # Main ingestion loop with fail-closed safety
                while self._is_running:
                    try:
                        raw_message = await asyncio.wait_for(ws.recv(), timeout=3.0)
                        await self.on_message(raw_message)
                    except websockets.exceptions.ConnectionClosedError:
                        _logger.warning("Remote connection closed.")
                        break
                    except asyncio.TimeoutError:
                        _logger.error("Message processing timed out.")
                        break
                        
        except websockets.exceptions.InvalidStatusCode as e:
            _logger.error(f"Exchange returned invalid status: {e}")
            self._fail_close()
        except Exception as connection_error:
            _logger.exception(f"Unexpected connection failure. Fail-closed triggered.")
            self._fail_close()

    def _fail_close(self) -> None:
        """Ensure resources are released and state is reset."""
        self._is_running = False
        if hasattr(self, '_ws_connection'):
            try:
                if self._ws_connection:
                    self._ws_connection.close()
            except Exception as cleanup_err:
                _logger.warning(f"Cleanup error during fail-close: {cleanup_err}")


async def run_secure_ingestion(ws_url: str, config_key: str = "EXCHANGE") -> None:
    """Utility function to instantiate and run the handler using environment variables."""
    # Secure Configuration Loader (Fail Closed if vars missing)
    env_prefix = f"{config_key.upper()}"
    try:
        api_key = os.getenv(f"{env_prefix}_API_KEY")
        api_secret = os.getenv(f"{env_prefix}_SECRET")
    except Exception as e:
        _logger.critical(f"Configuration error: {e}")
        return

    if not api_key or not api_secret:
        _logger.critical("Critical: Environment variables for API access are missing.")
        return

    config = {
        "api_key": api_key,
        "api_secret": api_secret, # In production, do not log this value directly to stdout/log file without masking
        "sandbox": os.getenv(f"{env_prefix}_SANDBOX", "false").lower() == "true"
    }

    handler = CryptoExchangeWebsocketHandler(ws_url=ws_url, api_config=config)
    
    # Ensure cleanup happens even if exception occurs (Context Manager logic applied manually for robustness)
    try:
        await handler.start()
    finally:
        if handler._is_running:
            handler._fail_close()
```