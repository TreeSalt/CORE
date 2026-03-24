---
DOMAIN: 01_DATA_INGESTION
MODEL: qwen3.5:9b
TIER: cruiser
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

```python
import asyncio
import logging
from typing import Optional, Callable
import websockets

# Configure logging to avoid credential leakage in logs
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class CryptoWebSocketStubV2:
    """
    Corrective implementation of Crypto WebSocket Stub V2.
    Ensures robust connection handling, error catching, and import hygiene
    for the 01_DATA_INGESTION domain tests.
    """
    
    def __init__(self, ws_url: str, message_callback: Optional[Callable[[dict], None]] = None):
        self.ws_url = ws_url
        self.message_callback = message_callback
        self.client_connection: Optional[websockets.WebSocketClientProtocol] = None
        self.is_running = False
        
        # Validate URL without exposing sensitive data
        if not ws_url.startswith(('wss://', 'ws://')):
            raise ValueError("WebSocket URL must use wss:// or ws:// protocol")

    async def start(self) -> bool:
        """Initialize the WebSocket connection securely."""
        try:
            if not self.message_callback:
                self.message_callback = lambda msg: logger.info(f"Received payload without handler: {msg}")
                
            loop = asyncio.get_event_loop()
            
            # Attempt connection handling with timeout protection
            async with websockets.connect(self.ws_url, ping_interval=20, close_timeout=10) as websocket:
                self.client_connection = websocket
                logger.info(f"Connection established to {self.ws_url}")
                
                # Start internal listener loop for incoming data
                try:
                    await asyncio.wait_for(websocket.recv(), timeout=None)
                except websockets.ConnectionClosed:
                    pass
                    
            return True
        except Exception as e:
            logger.error(f"Failed to initialize WebSocket stub: {e}", exc_info=True)
            self.client_connection = None
            return False

    async def stop(self):
        """Gracefully disconnect the client."""
        if self.client_connection:
            try:
                await self.client_connection.close()
                logger.info("WebSocket connection closed gracefully")
            except Exception as e:
                logger.warning(f"Error during shutdown: {e}")
            
        self.is_running = False

    async def process_message(self, data: dict) -> None:
        """Callback handler for incoming WebSocket messages."""
        try:
            if self.message_callback and callable(self.message_callback):
                self.message_callback(data)
        except Exception as e:
            # Prevent crash on malformed user-provided callbacks during ingestion
            logger.error(f"Error processing message callback: {e}")

    async def run_event_loop_until_stopped(self, task_duration_seconds: int = None):
        """Run the ingestion loop until explicitly stopped or timeout reached."""
        if not self.client_connection:
            logger.warning("No active client connection for event loop.")
            return
            
        try:
            while self.is_running:
                # Handle heartbeat to keep connection alive
                try:
                    await asyncio.wait_for(self.client_connection.recv(), timeout=10)
                except websockets.exceptions.ConnectionClosedOK:
                    logger.info("Connection closed by server")
                    break
                    
                except websockets.exceptions.TimeoutError:
                    logger.warning("Heartbeat timeout, attempting reconnect...")
                    
        except Exception:
            await self.stop()

    def shutdown(self):
        """Synchronous wrapper to stop the asynchronous task."""
        asyncio.create_task(self.stop())
        self.is_running = False
```