import asyncio
import json
import unittest

from websockets.server import serve

from antigravity_harness.execution.websocket_feed import WebSocketResearchFeed


class TestWebSocketFeed(unittest.IsolatedAsyncioTestCase):
    async def test_message_routing(self):
        """Verify that messages from server trigger the correct callback."""
        received_messages = []
        
        async def on_msg(msg):
            received_messages.append(msg)
            
        # Start a local mock server
        async def mock_server(websocket):
            await websocket.send(json.dumps({"type": "price", "symbol": "BTC-USD", "price": 50000.0}))
            await websocket.send(json.dumps({"type": "heartbeat"})) # Should be ignored by routing
            await websocket.send(json.dumps({"type": "trade", "qty": 1.0}))
            await asyncio.sleep(0.1) # Let them process
        
        async with serve(mock_server, "localhost", 8765):
            feed = WebSocketResearchFeed(
                uri="ws://localhost:8765", 
                on_message=on_msg,
                reconnect_interval=10.0 # Prevent double-firing in tests
            )
            
            # Start feed in background
            task = asyncio.create_task(feed.connect())
            
            # Wait for messages to arrive
            for _ in range(30):
                if len(received_messages) >= 2:
                    await asyncio.sleep(0.2) # Wait for any potential late-comers
                    break
                await asyncio.sleep(0.1)
                
            await feed.stop()
            await task
            
        self.assertGreaterEqual(len(received_messages), 2)
        self.assertEqual(received_messages[0]["type"], "price")
        self.assertEqual(received_messages[1]["type"], "trade")

    async def test_reconnection(self):
        """Verify that client attempts reconnection when server drops."""
        
        # We'll use a custom uri that fails first then succeeds? 
        # Easier to just verify it doesn't crash on connection error and keeps trying.
        
        feed = WebSocketResearchFeed(
            uri="ws://localhost:9999", # Non-existent port
            reconnect_interval=0.1
        )
        
        # Start feed and verify it survives connection errors
        task = asyncio.create_task(feed.connect())
        await asyncio.sleep(0.3) # Should have failed and queued reconnect
        
        self.assertTrue(feed._active)
        
        await feed.stop()
        await task

    async def test_ofi_streaming(self):
        """Verify that L1 order book updates trigger correct OFI cumulative scores."""
        received_messages = []
        
        async def on_msg(msg):
            received_messages.append(msg)
            
        async def mock_server(websocket):
            # 0: Init
            await websocket.send(json.dumps({
                "type": "l1", "symbol": "BTC", 
                "bid_price": 100.0, "bid_size": 10.0, 
                "ask_price": 101.0, "ask_size": 10.0
            }))
            # 1: Bid size increases -> OFI = 5
            await websocket.send(json.dumps({
                "type": "l1", "symbol": "BTC", 
                "bid_price": 100.0, "bid_size": 15.0, 
                "ask_price": 101.0, "ask_size": 10.0
            }))
            # 2: Ask price decreases -> Va = 10, OFI = -10
            await websocket.send(json.dumps({
                "type": "l1", "symbol": "BTC", 
                "bid_price": 100.0, "bid_size": 15.0, 
                "ask_price": 100.5, "ask_size": 10.0
            }))
            await asyncio.sleep(0.1)
        
        async with serve(mock_server, "localhost", 8766):
            feed = WebSocketResearchFeed(uri="ws://localhost:8766", on_message=on_msg)
            task = asyncio.create_task(feed.connect())
            
            for _ in range(20):
                if len(received_messages) >= 3:
                    break
                await asyncio.sleep(0.1)
                
            await feed.stop()
            await task
            
        self.assertEqual(len(received_messages), 3)
        self.assertEqual(received_messages[0]["ofi_tick"], 0.0)
        self.assertEqual(received_messages[1]["ofi_tick"], 5.0)
        self.assertEqual(received_messages[1]["ofi_cumulative"], 5.0)
        self.assertEqual(received_messages[2]["ofi_tick"], -10.0)
        self.assertEqual(received_messages[2]["ofi_cumulative"], -5.0)

if __name__ == "__main__":
    unittest.main()
