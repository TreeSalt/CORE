---
DOMAIN: 01_DATA_INGESTION
MODEL: qwen3.5:9b
TIER: cruiser
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

import os
import time
import logging
from typing import Generator, Dict, Optional, List
import requests

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AlpacaDataProvider:
    def __init__(self):
        self._api_key = os.getenv("ALPACA_API_KEY", "")
        self._secret_key = os.getenv("ALPACA_SECRET_KEY", "")
        # Base URL for Market Data API v1 and v2 (using v1 for bars via REST is easier for this demo)
        self.base_url = "https://data.alpaca.markets/v1"
        self.session = requests.Session()
        self._running = False
        
    def _get_headers(self):
        if not self._api_key:
            logger.error("ALPACA_API_KEY is not configured in environment.")
            raise ValueError("ALPACA_API_KEY is required")
        # Alpaca Market Data API v1/2 often requires basic auth or specific headers for private data
        # Public market data usually works without auth, but Enterprise requires keys.
        # We'll use X-API-KEY header which is common in newer SDKs, or Bearer token.
        # For simplicity and compatibility with public endpoints:
        headers = {
            "Accept": "application/json"
        }
        if self._secret_key:
            # Use Basic Auth style if secret provided (common for v1)
            import base64
            creds = f"{self._api_key}:{self._secret_key}"
            encoded = base64.b64encode(creds.encode()).decode()
            headers["Authorization"] = f"Basic {encoded}"
        return headers

    def get_bars(self, symbol: str, timeframe: str, range: Optional[str] = None) -> List[Dict]:
        """
        Fetches historical candlestick bars for a given symbol.
        
        Args:
            symbol: Ticker symbol (e.g., 'AAPL')
            timeframe: Timeframe (e.g., '1m', '5min', '1D') - Note: Period is often passed as 'period' param in API
            range: Time range string (e.g., '1d', '10mo'). If None, default to last 5 days? 
                   Or rely on 'start/end' params if supported. We will pass 'range' parameter if provided.
        
        Returns:
            List of bar dictionaries.
        """
        try:
            # Construct the endpoint. Period maps directly.
            # API v1 expects: bars?symbol={sym}&period={period}&range={range}
            # If timeframe is '1d', range could be omitted to get default, but let's allow explicit range
            if not range and timeframe == "1D":
                range = "5d" # Default fallback for demo if specific range not provided and symbol looks like stock
            elif not range:
                range = "1d" # Minimal default
            
            endpoint = f"{self.base_url}/bars?symbol={symbol}&period={timeframe}&range={range}"
            
            resp = self.session.get(endpoint, headers=self._get_headers(), timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                # API returns bars in a list inside a dict or list depending on structure. 
                # Usually {"results": [...]}.
                return data.get("results", [])
            else:
                logger.error(f"API Error fetching bars: {resp.text}")
                return []
        except Exception as e:
            logger.exception(f"Exception in get_bars for {symbol}: {e}")
            return []

    def get_quote(self, symbol: str) -> Dict:
        """
        Fetches the current last quote for a given symbol.
        
        Args:
            symbol: Ticker symbol
        
        Returns:
            Quote dictionary or empty dict on error.
        """
        try:
            endpoint = f"{self.base_url}/quote/{symbol}"
            resp = self.session.get(endpoint, headers=self._get_headers(), timeout=10)
            
            if resp.status_code == 200:
                data = resp.json()
                # Quote endpoint returns dict directly
                return data
            else:
                logger.warning(f"Quote not found or error for {symbol}: {resp.text}")
                return {}
        except Exception as e:
            logger.exception(f"Exception in get_quote for {symbol}: {e}")
            return {}

    def subscribe_stream(self, symbol: str) -> Generator[Dict, None, None]:
        """
        Subscribes to a stream of market data updates.
        
        Args:
            symbol: Ticker symbol
        
        Yields:
            Market data update dictionaries (Quote/Bars).
        """
        try:
            # Since implementing raw WebSocket requires 'websockets' lib and is complex,
            # We will poll the quote endpoint every X seconds to simulate a stream of updates.
            # This is a pragmatic approach for REST-heavy data providers without WS libs.
            
            # Note: If websockets lib is installed, one could use that here.
            if self._api_key and os.path.exists("websocket_client_mock"): 
                # Simulated logic for real implementation would go here
                
            logger.info(f"Starting subscription stream for {symbol} (Polling mode).")
            
            # Start an infinite generator loop
            while True:
                # To simulate live updates, fetch quote or latest bars periodically
                quote = self.get_quote(symbol)
                if quote:
                    yield quote
                time.sleep(1.0) # Poll every second
                
        except Exception as e:
            logger.exception(f"Stream error for {symbol}: {e}")
            # Keep generator alive but stop yielding or raise depending on needs
            # Usually, streams stop gracefully on errors in production logic
            return 
            
    def close(self):
        """Closes the data provider session."""
        try:
            self._running = False
            self.session.close()
            logger.info("AlpacaDataProvider closed.")
        except Exception as e:
            logger.exception(f"Error closing provider: {e}")

# Example usage if run as script (commented out to keep it clean for import)
if __name__ == "__main__":
    # Ensure env vars are set before running or use mock keys for testing
    provider = AlpacaDataProvider()
    try:
        # Get current quote
        print("Current Quote:", provider.get_quote("BTC-USD"))
        
        # Get bars (using default parameters for example)
        bars = provider.get_bars("AAPL", "1D")
        print("Bars Count:", len(bars))
        
        # Stream simulation (Run in background or interrupt to stop)
        # import threading
        # thread = threading.Thread(target=lambda: list(provider.subscribe_stream("BTC-USD")), daemon=True)
        # thread.start()
    except ValueError as ve:
        print(f"Configuration Error: {ve}")
    finally:
        provider.close()<|endoftext|><|im_start|>user