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
import base64

class AlpacaHarness:
    def __init__(self):
        self.api_key = os.getenv('ALPACA_API_KEY')
        self.api_secret = os.getenv('ALPACA_SECRET_KEY')
        
        if not self.api_key or not self.api_secret:
            raise RuntimeError("MANTIS CRITICAL: ALPACA_API_KEY and ALPACA_SECRET_KEY must be set in environment.")
            
        self.base_url = 'https://paper-api.alpaca.markets/v2'
        self.last_order_time = 0
        self.max_btc = 0.01
        self.log_path = './mantis_trade_log.json'

    def health_check(self):
        try:
            encoded_creds = base64.b64encode(f"{self.api_key}:{self.api_secret}".encode()).decode()
            headers = {
                'Authorization': f'Basic {encoded_creds}',
                'Accept': 'application/json' 
            }
            
            response = requests.get(f'{self.base_url}/account/status', headers=headers, timeout=5)
            if response.status_code != 200:
                return False
            time.sleep(1) # Add delay to be respectful
            return True
        except Exception:
            return False

    def fetch_bars(self, resolution='1D', end=''):
        try:
            symbol = 'bitcoin-btc-usd'
            params = {'symbol': symbol, 'resolution': resolution, 'end': end, 'limit': 500}
            
            response = requests.get(f'{self.base_url}/bars', params=params, headers=self._get_auth_header(), timeout=10)
            
            if response.status_code != 200:
                return None
                
            data = response.json()
            if not data or 'quotes' not in data:
                return []
            
            # Ensure all values are floats
            bars = [[float(v) for v in bar] for bar in data['quotes']]
            return bars
        except Exception:
            self._log_error("Error fetching bars")
            return None

    def get_position(self):
        try:
            response = requests.get(f'{self.base_url}/positions/GET', headers=self._get_auth_header(), timeout=10)
            if response.status_code != 200:
                return None
            
            data = response.json()
            
            snapshot = {
                'equity': float(data.get('account_equity', 0)),
                'buying_power': float(data.get('buying_power', 0)),
                'cash_buying_power': float(data.get('cash_buying_power', 0))
            }
            
            pos_list = data.get('positions', [])
            btc_pos = [p for p in pos_list if p.get('symbol') == 'bitcoin-btc-usd']
            if btc_pos:
                snapshot['btc_qty'] = float(btc_pos[0].get('qty', 0))
                snapshot['avg_entry_price'] = float(btc_pos[0].get('avg_entry_price', 0))
                
            return snapshot
        except Exception:
            self._log_error("Error getting position")
            return None

    def submit_order(self, qty):
        try:
            current_time = time.time()
            
            # Fail-closed logic for rapid-fire prevention (60s cooldown)
            if current_time - self.last_order_time < 60:
                self._log_error("Rate Limit Exceeded")
                return {"success": False, "error": "Rate Limit Exceeded"}
            
            symbol = 'bitcoin-btc-usd'
            params = {'symbol': symbol, 'qty': qty, 'side': 'buy', 'type': 'market', 'time_in_force': 'day'}
            
            response = requests.post(f'{self.base_url}/orders', json=params, headers=self._get_auth_header(), timeout=10)
            
            if response.status_code in [200, 201]:
                self.last_order_time = current_time
                
                log_entry = {
                    "timestamp": int(time.time()),
                    "type": "ORDER",
                    "success": True,
                    "order_id": response.json().get('id', ''),
                    "symbol": symbol,
                    "qty": qty
                }
                
                os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
                with open(self.log_path, 'a') as f:
                    json.dump(log_entry, f, ensure_ascii=False)
                    
                return {"success": True}
            else:
                self._log_error(f"Order failed with status {response.status_code}: {response.text}")
                self.last_order_time = current_time
                
                return {"success": False, "status": response.status_code}
                
        except Exception as e:
            self._log_error(f"Order exception: {str(e)}")
            return {"success": False, "error": str(e)}

    def _get_auth_header(self):
        encoded_creds = base64.b64encode(f"{self.api_key}:{self.api_secret}".encode()).decode()
        # Alpaca supports Basic Auth for these endpoints.
        headers = {
            'Authorization': f'Basic {encoded_creds}'
        }
        return headers

    def _log_error(self, message):
        try:
            with open(self.log_path, 'a') as f:
                entry = {
                    "timestamp": int(time.time()),
                    "type": "ERROR",
                    "message": message
                }
                json.dump(entry, f, ensure_ascii=False)
        except Exception:
            pass
```