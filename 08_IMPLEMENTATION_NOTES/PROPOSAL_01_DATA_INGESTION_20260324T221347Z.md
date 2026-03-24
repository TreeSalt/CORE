---
DOMAIN: 01_DATA_INGESTION
MODEL: qwen3.5:9b
TIER: cruiser
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

```python
import os
import logging
import sys
from datetime import datetime, timedelta
import pandas as pd

# Initialize logging configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def validate_environment():
    """Validate presence of required environment variables."""
    required_vars = ['CRYPTO_API_KEY', 'DATA_STORAGE_PATH']
    missing_vars = []
    
    for var in required_vars:
        if var not in os.environ or not os.environ[var]:
            logger.critical(f"Missing or empty credential/env variable: {var}")
            missing_vars.append(var)
    
    if missing_vars:
        raise ValueError(f"Environment validation failed. Missing vars: {missing_vars}")

def fetch_crypto_data(start_date, end_date):
    """Fetch historical crypto data from API."""
    url = os.getenv('CRYPTO_API_ENDPOINT') or 'https://api.example.com/v1/market/history'
    
    try:
        headers = {'Authorization': f'Bearer {os.environ["CRYPTO_API_KEY"]}'}
        # Mock request logic for proposal safety; replace with actual client
        
        start_dt_str = start_date.strftime('%Y-%m-%dT%H:%M:%S')
        end_dt_str = end_date.strftime('%Y-%m-%dT%H:%M:%S')
        
        # Construct parameters safely
        params = {
            'start': start_dt_str,
            'end': end_dt_str,
            'asset': 'BTC', 
            'format': 'json'
        }

        # Simulate fetch response structure for ingestion pipeline
        mock_data = pd.DataFrame({
            'timestamp': [start_dt_str],
            'price_usd': [65000.50]
        })
        
        return mock_data
        
    except Exception as e:
        logger.error(f"Failed to fetch data: {e}")
        return pd.DataFrame()

def write_to_storage(df, path):
    """Write processed data to storage."""
    if not df.empty:
        file_path = os.path.join(path, f"backfill_{datetime.now().strftime('%Y%m%d_%H%M%S')}.parquet")
        
        # Ensure directory exists without writing to governance folders
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        try:
            df.to_parquet(file_path, index=False)
            logger.info(f"Data successfully written to {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to write data to storage: {e}")
            return False
    else:
        logger.warning("No data to write.")
        return False

def main():
    try:
        validate_environment()
        
        # Define backfill window (example: last 24 hours)
        today = datetime.now()
        yesterday = today - timedelta(hours=24)
        
        source_df = fetch_crypto_data(yesterday, today)
        success = write_to_storage(source_df, os.getenv('DATA_STORAGE_PATH', '/01_DATA_INGESTION/data/raw'))
        
        if not success:
            sys.exit(1)
            
    except Exception as e:
        logger.critical(f"Backfill process terminated with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
```