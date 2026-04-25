---
DOMAIN: 00_PHYSICS_ENGINE
MODEL: qwen3.5:9b
TIER: cruiser
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

```python
import os
import time
import json
import requests
from dataclasses import dataclass

@dataclass
class PositionSnapshot:
    equity: float
    buying_power: float
    qty: int = 0
    
# Default base URL if not provided via env var
BASE_URL = os.environ.get('ALPACA_API_BASE_URL', 'https://paper-api.alpaca.markets')

class AlpacaHarness:
    def __init__(self):
        self.session = requests.Session()
        self.base_url = BASE_URL # Default from env or standard paper URL logic
        
        if not self.base_url.startswith('http'):
             raise ValueError("Base URL must be an http(s) string")

    def health_check(self) -> bool:
        try:
            resp = self.session.get(f"{self.base_url}/v2/health", timeout=5)
            if resp.status_code != 200: 
                return False # Or raise? Prompt says "fail closed" on exception. Status code isn't an exception.
                # Usually status codes are checked before raising. I'll just return False here or Raise if API is truly down (5xx).
            # Assuming simple check:
            data = resp.json()
            return 'status' in data and data['status'] == 'ok'
        except Exception:
             raise # Fail closed on network issues

    def fetch_bars(self, timeframe: str, limit: int = 100):
        try:
            resp = self.session.get(f"{self.base_url}/v2/ohlc/btc/usd", timeout=5, 
                params={"symbols": "bitcoin", "timeframe": timeframe, "limit": limit} # Prompt instruction
            )
            
            if resp.status_code != 200: raise Exception("Status error")
            return resp.json() # Return raw json which should be list of OHLCV data
            
        except Exception as e:
             raise

    def get_position(self) -> PositionSnapshot:
        try:
            pos_resp = self.session.get(f"{self.base_url}/v2/accounts/self/positions", timeout=5)
            acc_resp = self.session.get(f"{self.base_url}/v2/accounts/self/account_status", timeout=5)
            
            if pos_resp.status_code != 200 or acc_resp.status_code != 200: raise Exception("API Status Code Error")
            
            acc_data = acc_resp.json()
            pos_list = pos_resp.json()
            
            equity = float(acc_data.get('equity', 0))
            buying_power = float(acc_data.get('buying_power', 0))
            qty = sum(float(p['qty']) for p in pos_list) # Simple sum
            
            return PositionSnapshot(equity=equity, buying_power=buying_power, qty=int(qty))
            
        except Exception as e:
             raise

    def submit_order(self, side: str) -> bool:
        try:
            if time.time() - self._last_order_time < 60: # Rate limit check (safety for looped calls)
                return False
            
            order_data = {
                "symbol": "BTCUSD",
                "qty": 1,
                "side": side, 
                "type": "market",
                "time_in_force": "day"
            }
            
            resp = self.session.post(f"{self.base_url}/v2/orders", json=order_data, timeout=5)
            
            if resp.status_code != 200: raise Exception(f"Order failed with {resp.status_code}")
            
            order_info = resp.json()
            status = order_info.get('status', 'unknown')
            
            # Log to file
            log_entry = {
                "timestamp": time.time(),
                "symbol": order_info['symbol'], 
                "side": side, 
                "status": status,
                "msg": f"Order {status}" # Context
            }
            
            with open("mantis_trade_log.json", 'a') as f:
                 json.dump(log_entry, f)
                 
            self._last_order_time = time.time() # Reset wait timer
            
            return True 
            
        except Exception as e:
             raise # Fail closed on error

```