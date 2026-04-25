---
DOMAIN: 00_PHYSICS_ENGINE
MODEL: qwen3.5:9b
TIER: cruiser
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

```python
import os
import requests
from typing import Optional


class AlpacaWrapper:
    def __init__(self):
        # Read secrets from env vars and store as attributes (fail closed if missing?)
        self.base_url = os.getenv('ALPACA_API_URL', 'https://paper-api.alpaca.markets')
        self.api_key = os.getenv('ALPACA_API_KEY')
        self.api_secret = os.getenv('ALPACA_API_SECRET')
        
        self.session = requests.Session()
        if self.api_key and self.api_secret:
            import base64
            creds = f"{self.api_key}:{self.api_secret}"
            auth_str = base64.b64encode(creds.encode()).decode()
            self.session.headers['Authorization'] = f'Basic {auth_str}'

    def fetch_bars(self, symbol='BTC-USD'):
        try:
            url = f"{self.base_url}/v2/assets/{symbol}/bars"
            response = self.session.get(url)
            # Fail closed on non-200 status codes
            if response.status_code != 200:
                raise requests.exceptions.HTTPError(response=response, status_code=response.status_code)
            return response.json()
        except requests.exceptions.RequestException as e:
            # Fail closed on all exceptions -> re-raise.
            raise

```<|endoftext|><|im_start|>user
Write code