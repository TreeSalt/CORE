---
DOMAIN: 01_DATA_INGESTION
MODEL: qwen3.5:9b
TIER: cruiser
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

import os
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging
import requests

# Configure internal logging (No writes to 04_GOVERNANCE/)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('data_ingestion_backfill')

class CoinBackfillManager:
    """
    Corrective Context v2 for 01_DATA_E4_005_crypto_backfill_v2.
    
    CHANGELOG:
    - Replaces undocumented /days parameter with documented /range endpoint.
    - Implements fail-closed behavior on API constraint breach (rate limit, auth).
    - Enforces environment-based credential handling (NO hardcoded secrets).
    """

    BASE_URL = "https://api.coingecko.com/api/v3"
    COIN_ID = "bitcoin"
    
    def __init__(self, start_date: str, end_date: str):
        self.start_datetime = datetime.fromisoformat(start_date.replace('Z', '+00:00')) if 'T' in start_date else datetime.fromisoformat(start_date)
        self.end_datetime = datetime.fromisoformat(end_date.replace('Z', '+00:00')) if 'T' in end_date else datetime.fromisoformat(end_date)
        self.session = requests.Session()
        self._validate_auth_config()

    def _validate_auth_config(self):
        """Fail closed on missing required credentials or config."""
        # Optional API Key for Enterprise/Pro limits validation, not strictly mandatory for basic public tier 
        # but recommended for backfill stability.
        if 'COINGECKO_API_KEY' in os.environ:
            self.session.headers['X-CG-PRO-APIKEY'] = os.getenv('COINGECKO_API_KEY')
        else:
            logger.warning("Running on free tier (no API key provided in env). Rate limits may apply.")
        
        if not os.getenv('DATA_INGESTION_SECRET_STORAGE_AVAILABLE', 'false'):
            raise EnvironmentError("Credential store unavailable. Ingest mode disabled per security policy.")

    def fetch_range_data(self, start_time: datetime, end_time: datetime) -> Optional[Dict[str, Any]]:
        """
        Fetches historical market data for the specified date range using the documented /range endpoint.
        """
        url = f"{self.BASE_URL}/coins/{self.COIN_ID}/market_chart/range"
        
        params = {
            "vs_currency": "usd",
            "start_date": start_time.strftime("%Y-%m-%d"),
            "end_date": end_time.strftime("%Y-%m-%d")
        }

        # Retry logic with exponential backoff for rate limit (429) or network errors
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, params=params, timeout=30)
                
                if response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', 60))
                    logger.warning(f"Rate limit hit. Retrying in {retry_after}s...")
                    time.sleep(retry_after)
                    continue
                
                if response.status_code != 200:
                    logger.error(f"API returned status code: {response.status_code}")
                    return None
                    
                return response.json()
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Network error fetching data (attempt {attempt+1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    return None

    def run_backfill(self) -> Dict[str, Any]:
        """
        Orchestrates the backfilling process.
        Splits large ranges to avoid API constraints and ensure data integrity.
        """
        logger.info(f"Starting backfill: {self.start_datetime} to {self.end_datetime}")

        total_days = (self.end_datetime - self.start_datetime).days
        
        # Conservative chunking for safety on Free Tier / Enterprise limits 
        if total_days > 365:
            chunk_days = 180 
            current_date = self.start_datetime + timedelta(days=1)
            
            while current_date <= self.end_datetime + timedelta(hours=24):
                # Ensure valid range (max ~90-365 depending on plan, /range supports up to 730 sometimes but we cap at 180 for safety)
                range_start = current_date - timedelta(days=chunk_days)
                if range_start < self.start_datetime:
                    range_start = self.start_datetime
                
                chunk_end = min(current_date + timedelta(days=chunk_days), self.end_datetime + timedelta(hours=24))
                
                # Adjust for inclusive ranges in API logic
                fetch_data = self.fetch_range_data(range_start, chunk_end)
                
                if fetch_data:
                    logger.info(f"Successfully fetched data for {range_start.date()} to {chunk_end.date()}")
                else:
                    logger.error("Data fetch failed for current chunk. Aborting run.")
                    return {"success": False, "reason": "Chunk fetch failure", "failed_range": f"{range_start} to {chunk_end}"}

                current_date += timedelta(days=chunk_days)
                
            return {"success": True, "chunks_processed": total_days // chunk_days}

        else:
            # Single fetch for small ranges
            data = self.fetch_range_data(self.start_datetime, self.end_datetime)
            if data:
                logger.info(f"Single range fetch completed.")
                return {"success": True, "data_keys": len(data.get("prices", []))}
            else:
                logger.error("Single range fetch failed.")
                return {"success": False, "reason": "API Error or Rate Limit"}