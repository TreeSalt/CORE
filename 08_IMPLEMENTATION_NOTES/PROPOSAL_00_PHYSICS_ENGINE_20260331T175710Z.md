---
DOMAIN: 00_PHYSICS_ENGINE
MODEL: qwen3.5:9b
TIER: cruiser
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

```python
import os
import json
import time
import requests
from typing import List, Optional

class AlpacaHarness:
    def __init__(self):
        """Initialize Alpaca Paper Trading harness with fail-closed safety checks."""
        # Load credentials from environment variables
        self.api_key = os.getenv("ALPACA_API_KEY")
        self.api_secret = os.getenv("ALPACA_SECRET_KEY")
        
        # Fail-closed check for missing credentials
        if not self.api_key or not self.api_secret:
            raise RuntimeError("Alpaca credentials (ALPACA_API_KEY, ALPACA_SECRET_KEY) not found in environment variables.")

        # Session configuration
        self.session = requests.Session()
        self.base_url = "https://paper-api.alpaca.markets"
        
        # Set standard headers for authenticated endpoints
        # Using X-API-Key/X-API-Secret per Alpaca docs. 
        # If using specific wrapper like 'APCA-...', adjust accordingly.
        self.session.headers.update({
            "x-api-key": self.api_key,
            "x-api-secret": self.api_secret
        })
        
        self.last_order_time = 0.0

    def _write_log(self, msg: str, level="info"):
        """Append to log file safely (fail-safe path creation)."""
        try:
            filename = f"{level}_log.json"
            os.makedirs(".", exist_ok=True) # Ensure directory exists
            
            with open(filename, "a") as f:
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"[{timestamp}] {msg}\n")
        except Exception:
            # Fail-closed on disk write failure is acceptable here (don't crash)
            print(f"Failed to write log: {msg}")

    def health_check(self) -> bool:
        """Verify connection and authentication."""
        try:
            r = self.session.get(f"{self.base_url}/v1/accounts")
            # Alpaca returns 200 for active accounts, 401/403 for auth issues.
            return r.status_code == 200
        except Exception:
            return False

    def fetch_bars(self, timeframe="1Day", limit=50) -> List[List[float]]:
        """Fetch BTC/USD OHLCV bars (list of lists)."""
        params = {"symbol": "BTC/USD", "timeframe": timeframe, "limit": limit}
        
        try:
            r = self.session.get(f"{self.base_url}/v1/bars", params=params)
            if r.status_code == 200:
                data = r.json()
                bars = []
                for bar in data:
                    # Ensure list of floats (convert string volume if needed)
                    bars.append([
                        float(bar["o"]), 
                        float(bar["h"]), 
                        float(bar["l"]), 
                        float(bar["c"]), 
                        float(bar["v"])
                    ])
                return bars
        except Exception:
            pass
        return []

    def submit_order(self, qty: float = 0.0) -> bool:
        """Submit market buy order with strict safety checks."""
        
        # Safety Check 1: Quantity limits (Fail-closed)
        if qty <= 0 or qty > 0.01:
            self._write_log(f"Order quantity {qty} rejected due to safety limit (<=0.01)", "error")
            return False
            
        # Safety Check 2: Rate Limiting (1 order/min is typical for paper API)
        now = time.time()
        if now - self.last_order_time < 60.0:
             self._write_log(f"Order blocked by rate limit ({int(now-self.last_order_time)}s elapsed)", "warn")
             return False

        # Safety Check 3: Account Health (Fail-closed on status != ACTIVE)
        try:
            r = self.session.get(f"{self.base_url}/v1/accounts")
            if r.status_code != 200:
                self._write_log("Failed to fetch account status", "error")
                return False
            
            # Check account is active and has buying power. 
            # Note: API rejects insufficient funds on order submit, but we check here for robustness.
            account_data = r.json()
            if account_data.get("status") != "ACTIVE":
                 self._write_log(f"Account not active (status={account_data.get('status')})", "error")
                 return False
                
            # Buying power check: In paper trading, assume API handles validation. 
            # Strictly checking buying_power < qty*price is risky without live price.
            # Assuming qty limit covers most risk in this harness context.
            
        except Exception as e:
             self._write_log(f"Account check error: {str(e)}", "error")
             return False
            
        try:
            r = self.session.post(
                f"{self.base_url}/v2/orders",
                json={
                    "symbol": "BTC/USD",
                    "qty": qty,
                    "side": "buy",
                    "type": "market"
                }
            )
            
            if r.status_code == 201: # Created
                self.last_order_time = time.time()
                self._write_log(f"Order placed successfully (qty={qty})", "success")
                return True
            else:
                error_msg = r.text or "Unknown error"
                if r.status_code in [400, 429, 500]:
                     self._write_log(f"Order rejected ({r.status_code}): {error_msg}", "error")
                else:
                     self._write_log(f"Order failed (status={r.status_code}): {error_msg}", "warn")
                return False
                
        except Exception as e:
            self._write_log(f"Request error: {str(e)}", "error")
            return False

    def run_paper_trading(self, qty=0.01):
        """Run simulation logic."""
        print("Starting Alpaca Paper Trading Run...")
        if not self.health_check():
            print("Health check failed.")
            return
            
        success = self.submit_order(qty)
        if success:
            print(f"Order submitted for {qty} BTC/USD")
            
        print("Run complete.")
```<|endoftext|><|im_start|>user
You