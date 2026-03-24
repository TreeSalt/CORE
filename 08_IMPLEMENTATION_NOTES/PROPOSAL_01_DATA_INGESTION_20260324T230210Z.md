---
DOMAIN: 01_DATA_INGESTION
MODEL: qwen3.5:9b
TIER: cruiser
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

```python
# src/modules/data_ingestion/paper_trade_harness.py

import asyncio
import logging
from typing import Optional, Dict, Any, Callable
import websockets
from datetime import datetime

# Configure logging to avoid writing to governance directories or sensitive logs
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger(__name__)


class DataIngestionError(Exception):
    """Custom exception for data ingestion failures."""
    pass


class PaperTradeHarness:
    def __init__(self, config_dict: Dict[str, Any]) -> None:
        """
        Initialize the Paper Trade Harness.
        
        Args:
            config_dict: Configuration dictionary (URLS, IDs, etc.). 
                         Must NOT contain hardcoded credentials or secrets.
        """
        self.config = config_dict
        self.connection: Optional[websockets.WebSocketClientProtocol] = None
        self.is_running = False
        self.retries: int = 3
        self.retry_delay: float = 2.0
        
        # Ensure no sensitive data is logged directly
        self._sanitize_config()

    def _sanitize_config(self) -> None:
        """Remove or redact potential credentials from logging config."""
        forbidden_keys = ['password', 'secret', 'api_key', 'token']
        for key in forbidden_keys:
            if key in self.config and isinstance(self.config[key], str):
                logger.warning(f"Configuration key '{key}' detected but masked.")
                self.config[key] = "REDACTED"

    async def connect(self) -> bool:
        """Establish WebSocket connection with retry logic."""
        url = self.config.get("websocket_url", "")
        if not url:
            raise DataIngestionError("WebSocket URL is required in configuration.")
        
        logger.info(f"Attempting connection to {url[:20]}...")

        for attempt in range(self.retries):
            try:
                self.connection = await websockets.connect(
                    url,
                    ping_interval=20,
                    ping_timeout=20
                )
                logger.info("WebSocket connection established successfully.")
                return True
            except OSError as e:
                if attempt == self.retries - 1:
                    logger.error(f"Failed to connect after {self.retries} attempts: {e}")
                    raise DataIngestionError(f"Persistent connection failure: {e}")
                logger.warning(f"Connection attempt {attempt + 1} failed. Retrying in {self.retry_delay}s...")
                await asyncio.sleep(self.retry_delay)

        return False

    async def ingest_message(self, message_data: Dict[str, Any]) -> bool:
        """Process incoming message data."""
        try:
            timestamp = datetime.utcnow().isoformat()
            
            # Simulate processing logic that would validate payload structure
            if "payload" not in message_data:
                logger.warning("Message lacks 'payload' key.")
                return False
                
            logger.info(f"Ingested payload snippet: {message_data.get('payload', '')[:50]}...")
            
            # Placeholder for processing logic
            return True

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            raise DataIngestionError(f"Message ingestion failed: {e}")

    async def close(self) -> None:
        """Gracefully close the harness."""
        self.is_running = False
        if self.connection and not self.connection.closed:
            await self.connection.close()
            logger.info("WebSocket connection closed gracefully.")

    async def run_stream(self, message_processor: Callable[[Dict[str, Any]], Dict[str, Any]]):
        """Run the continuous ingestion loop."""
        try:
            while self.is_running:
                if not self.connection or self.connection.closed:
                    logger.info("Connection lost. Attempting reconnection.")
                    await self.connect()

                try:
                    async for message in self.connection:
                        msg_dict = message.decode("utf-8")  # Convert bytes to string safely
                        data_payload = {"raw": msg_dict}
                        
                        try:
                            result = await self.ingest_message(data_payload)
                            if result:
                                logger.info("Ingestion successful.")
                        except DataIngestionError:
                            continue # Continue stream on ingestion failure
                            
                except websockets.exceptions.ConnectionClosedOK:
                    logger.info("Connection closed normally by server.")
        except Exception as e:
            logger.exception(f"Critical harness error: {e}")
```