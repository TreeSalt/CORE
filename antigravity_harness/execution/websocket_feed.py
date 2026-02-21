"""
antigravity_harness/execution/websocket_feed.py
==============================================
WebSocket Research Feed — real-time market data ingestion client.
Enables high-fidelity data collection and monitoring for research.
"""

import asyncio
import inspect
import json
import logging
from typing import Any, Callable, Dict, Optional

import websockets
from websockets.exceptions import ConnectionClosed

logger = logging.getLogger("WEBSOCKET_FEED")

class WebSocketResearchFeed:
    """
    Robust WebSocket client for market data research.
    Handles connection lifecycle, heartbeats, and message routing.
    """

    def __init__(
        self, 
        uri: str, 
        on_message: Optional[Callable[[Dict[str, Any]], None]] = None,
        reconnect_interval: float = 5.0
    ):
        self._uri = uri
        self._on_message = on_message
        self._reconnect_interval = reconnect_interval
        self._active = False
        self._websocket: Optional[websockets.WebSocketClientProtocol] = None

    async def connect(self) -> None:
        """Main execution loop with automatic reconnection."""
        self._active = True
        logger.info(f"Connecting to feed: {self._uri}")
        
        while self._active:
            try:
                async with websockets.connect(self._uri) as websocket:
                    self._websocket = websocket
                    logger.info("✅ WebSocket connected.")
                    await self._handle_messages()
            except (ConnectionClosed, OSError, Exception) as e:
                if not self._active:
                    break
                logger.warning(f"⚠️ Connection lost: {e}. Reconnecting in {self._reconnect_interval}s...")
                await asyncio.sleep(self._reconnect_interval)

    async def stop(self) -> None:
        """Gracefully stop the feed."""
        self._active = False
        if self._websocket:
            await self._websocket.close()
            logger.info("WebSocket stopped.")

    async def _handle_messages(self) -> None:
        """Internal message processing loop."""
        if not self._websocket:
            return

        async for message in self._websocket:
            try:
                payload = json.loads(message)
                
                # Check for control messages (e.g., heartbeats)
                if payload.get("type") == "heartbeat":
                    logger.debug("Received heartbeat.")
                    continue
                
                # Route to callback
                if self._on_message:
                    if inspect.iscoroutinefunction(self._on_message):
                        await self._on_message(payload)
                    else:
                        self._on_message(payload)
                        
            except json.JSONDecodeError:
                logger.error(f"Malformed JSON message: {message}")
            except Exception as e:
                logger.error(f"Error handling message: {e}")

    async def send(self, data: Dict[str, Any]) -> None:
        """Send a control message to the server."""
        if self._websocket and self._websocket.open:
            await self._websocket.send(json.dumps(data))
        else:
            logger.error("Attempted to send over closed WebSocket.")
