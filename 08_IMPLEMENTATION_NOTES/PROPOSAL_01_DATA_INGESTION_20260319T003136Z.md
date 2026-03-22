---
DOMAIN: 01_DATA_INGESTION
MODEL: qwen3.5:27b
TIER: heavy
TYPE: IMPLEMENTATION
STATUS: RATIFIED
---

```python
import urllib.request
import json
import csv
import pathlib
import datetime
import time
import sys

def fetch_and_store_crypto_data():
    # Configuration Constants
    API_URL = "https://api.binance.com/api/v3/klines"
    SYMBOL = "BTCUSDT"
    INTERVAL = "5m"
    LIMIT = 1000
    OUTPUT_FILE = pathlib.Path("data/crypto/BTCUSDT_5m.csv")
    
    # Retry Configuration
    MAX_RETRIES = 3
    RETRY_DELAY = 5
    
    # Ensure directory structure exists
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    # Determine the last processed timestamp to avoid duplicates
    last_timestamp = 0
    if OUTPUT_FILE.exists():
        try:
            with open(OUTPUT_FILE, 'r', newline='') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                if rows:
                    # The last row contains the latest timestamp
                    last_timestamp = int(rows[-1]['timestamp'])
        except Exception as e:
            print(f"Warning: Could not read existing file history. Starting from scratch or appending blindly.", file=sys.stderr)

    # Fetch Data with Retry Logic
    response_data = None
    query_params = f"?symbol={SYMBOL}&interval={INTERVAL}&limit={LIMIT}"
    full_url = API_URL + query_params
    
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            print(f"Fetching data (Attempt {attempt}/{MAX_RETRIES})...", file=sys.stderr)
            with urllib.request.urlopen(full_url, timeout=10) as response:
                raw_data = response.read().decode('utf-8')
                response_data = json.loads(raw_data)
                break # Success, exit retry loop
        except Exception as e:
            if attempt == MAX_RETRIES:
                print(f"Error: Failed to fetch data after {MAX_RETRIES} attempts. Reason: {e}", file=sys.stderr)
                sys.exit(1)
            time.sleep(RETRY_DELAY)

    if not response_data:
        print("Error: No valid data received from API.")
        return

    # Parse and Filter Candles
    new_candles = []
    for item in response_data:
        # API Kline Structure: [timestamp, open, high, low, close, volume, ...]
        candle_ts = int(item[0])
        
        # Only process candles strictly newer than the last stored one
        if candle_ts > last_timestamp:
            new_candles.append({
                "timestamp": candle_ts,
                "open": float(item[1]),
                "high": float(item[2]),
                "low": float(item[3]),
                "close": float(item[4]),
                "volume": float(item[5])
            })

    # Write Data to CSV
    # 'w' (write) mode overwrites if creating new file. 'a' (append) adds to existing.
    write_mode = 'w' if not OUTPUT_FILE.exists() else 'a'
    
    with open(OUTPUT_FILE, write_mode, newline='') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        
        # Write header only if creating a new file
        if write_mode == 'w':
            writer.writeheader()
            
        for candle in new_candles:
            writer.writerow(candle)

    # Generate Summary Statistics
    print("-" * 30)
    print(f"Candles added: {len(new_candles)}")
    
    if new_candles:
        start_ts = new_candles[0]['timestamp']
        end_ts = new_candles[-1]['timestamp']
        start_dt = datetime.datetime.fromtimestamp(start_ts / 1000.0)
        end_dt = datetime.datetime.fromtimestamp(end_ts / 1000.0)
        print(f"Date range: {start_dt.strftime('%Y-%m-%d %H:%M')} to {end_dt.strftime('%Y-%m-%d %H:%M')}")
    else:
        print("Date range: No new data found.")

    # File statistics
    file_size = OUTPUT_FILE.stat().st_size if OUTPUT_FILE.exists() else 0
    print(f"File size: {file_size} bytes")

if __name__ == "__main__":
    fetch_and_store_crypto_data()
```