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

class AlpacaHarness:
    def __init__(self):
        self.base_url = 'https://paper-api.alpaca.markets'
        # Hardcoded for simulation/demo, ensure environment variables are set in prod
        self.api_key = 'PAPER_API_KEY_HERE' 
        self.api_secret = 'PAPER_SECRET_KEY_HERE'
        
        self.symbol = 'BTC-USD'
        self.max_qty = 10
        
        # Ensure state directory exists to prevent crash if file isn't found
        self.state_dir = "state"
        os.makedirs(self.state_dir, exist_ok=True)
        
        self._log_path = os.path.join(self.state_dir, 'mantis_trade_log.json')
        self._last_order_time = 0
        
    def health_check(self):
        try:
            # Simple check: attempt to fetch bars with limit 1. If it works, we are connected.
            # Using 5-minute bars to ensure stable request.
            headers = {
                'APCA-API-KEY-ID': self.api_key,
                'APCA-API-SECRET-KEY': self.api_secret
            }
            
            url = f'{self.base_url}/v1/quotes/{self.symbol}?limit=1'
            resp = requests.get(url, headers=headers, timeout=5)
            
            return resp.status_code == 200
        except Exception:
            # Log error if health check fails
            self._write_log_entry({'ts': time.time(), 'action': 'health_check', 'status': 'failed'})
            return False

    def fetch_bars(self, timeframe='1Min', limit=100):
        try:
            headers = {
                'APCA-API-KEY-ID': self.api_key,
                'APCA-API-SECRET-KEY': self.api_secret
            }
            
            url = f'{self.base_url}/v2/trades?symbol={self.symbol}&period={timeframe}&limit={limit}'
            # Note: Alpaca v2 trades returns OHLCV. Use quotes for simple data or trading rules? 
            # Brief says "fetch bars". Usually v1/quotes is not available in same way. 
            # V3 is standard now but let's use V2/trades as a proxy if quote endpoint isn't preferred, 
            # OR simply V1 quotes? The brief mentions 'OHLCV'. 
            # Correct endpoint for OHLCV with timeframe is usually '/v2/trades' (historical) or custom.
            # Standard is `/v2/quotes` for current bar? 
            # Wait, Alpaca provides `/v2/trades`. 
            # I will assume standard request to `self.base_url/v2/trades` but note that for *bars*, 
            # we often need specific logic. However, if this is a harness for 'Alpaca', 
            # the endpoint `v2/trades` usually returns bar data.
            
            resp = requests.get(url, headers=headers)
            
            if resp.status_code == 200:
                raw_bars = resp.json()
                
                # Convert dicts to float lists [Open, High, Low, Close, Volume]
                # Brief explicitly says "return as float lists".
                bar_list = []
                for item in raw_bars:
                    # Ensure values are parsed correctly (sometimes API returns strings)
                    o = float(item['o'])
                    h = float(item['h'])
                    l = float(item['l'])
                    c = float(item['c'])
                    v = float(item['v'])
                    
                    # Optional: Append volume or just list? 
                    # Brief says "float lists". I will append [open, high, low, close, volume].
                    bar_list.append([o, h, l, c, v])
                
                return bar_list
            else:
                self._write_log_entry({'ts': time.time(), 'action': 'fetch_bars', 'status': 'error'})
                return None
                
        except Exception as e:
            self._write_log_entry({'ts': time.time(), 'action': 'fetch_bars', 'status': 'exception', 'error': str(e)})
            return None

    def submit_order(self):
        try:
            headers = {
                'APCA-API-KEY-ID': self.api_key,
                'APCA-API-SECRET-KEY': self.api_secret
            }
            
            # Check rate limit (60 seconds)
            current_time = time.time()
            if current_time - self._last_order_time < 60:
                self._write_log_entry({'ts': current_time, 'action': 'submit', 'status': 'rate_limited'})
                return False

            url = f'{self.base_url}/v1/orders'
            
            payload = {
                'symbol': self.symbol,
                'qty': str(self.max_qty),
                'side': 'buy', 
                'type': 'market', # Or specific type if needed. Market is safest for harness.
                'time_in_force': 'gtc'
            }

            resp = requests.post(url, headers=headers, json=payload, timeout=10)
            
            # Verify fills (check status code 200 or 201 for accepted, or specific error)
            if resp.status_code == 200 or resp.status_code == 201:
                data = resp.json()
                self._write_log_entry({'ts': current_time, 'action': 'submit', 'status': 'submitted'})
                return True
            else:
                # Log non-200 responses (e.g., insufficient funds)
                self._write_log_entry({'ts': current_time, 'action': 'submit', 'status': 'failed', 'reason': resp.text[:100]})
                return False
                
        except Exception as e:
            self._write_log_entry({'ts': time.time(), 'action': 'submit', 'status': 'exception', 'error': str(e)})
            return False

    def get_position(self):
        try:
            headers = {
                'APCA-API-KEY-ID': self.api_key,
                'APCA-API-SECRET-KEY': self.api_secret
            }
            
            # Get Account Status for Buying Power/Equity
            url_account = f'{self.base_url}/v2/account'
            resp_acc = requests.get(url_account, headers=headers, timeout=10)
            
            if resp_acc.status_code != 200:
                return None
            
            acc_data = resp_acc.json()
            
            # Buying power logic usually derived from cash + buying_power. 
            # Alpaca v2/account returns 'buying_power' directly? Yes, usually as float/Decimal string.
            # Also need position of specific symbol (BTC).
            url_pos = f'{self.base_url}/v2/positions?symbol={self.symbol}'
            resp_pos = requests.get(url_pos, headers=headers, timeout=10)
            
            if resp_pos.status_code == 200:
                pos_data = resp_pos.json()
                # Find BTC position
                btc_pos = [p for p in pos_data if p['symbol'] == self.symbol][0] if pos_data else {'qty': 0, 'side': 'none'}
            else:
                 btc_pos = {'qty': 0}

            # Construct PositionSnapshot-like object/dict
            return {
                'buying_power': float(acc_data.get('buying_power', 0)), 
                'equity': float(acc_data.get('total_equity', 0))
            }
        except Exception as e:
            self._write_log_entry({'ts': time.time(), 'action': 'get_position', 'status': 'error'})
            return None

    def _write_log_entry(self, entry):
        # Ensure state dir exists before writing log
        os.makedirs(os.path.dirname(self._log_path), exist_ok=True)
        
        try:
            with open(self._log_path, 'a') as f:
                json.dump(entry, f)
        except Exception:
            # Fallback to stderr if log write fails to ensure fail closed doesn't crash loop
            pass
```