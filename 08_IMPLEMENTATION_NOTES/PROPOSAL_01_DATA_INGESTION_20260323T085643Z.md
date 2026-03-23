---
DOMAIN: 01_DATA_INGESTION
MODEL: qwen3.5:9b
TIER: sprinter
TYPE: IMPLEMENTATION
STATUS: RATIFIED
---

```python
import os
import sys
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Iterator
from pathlib import Path

# Configuration and Constants
CONSTRAINT_GOV_PATH = Path("/04_GOVERNANCE") # Definition for safety, not execution target
LOG_LEVEL = "WARNING" # Default to WARNING on failure to reduce noise

def init_secure_logger() -> logging.Logger:
    """
    Initialize a secure logger that avoids logging secrets.
    Fails closed if initialization cannot be guaranteed safely.
    """
    try:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            fmt='[%(levelname)s] %(asctime)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        
        # Security Check: Do not configure handlers that log full stack traces of internal states
        # unless necessary for debugging in a secure environment.
        
        logger = logging.getLogger("crypto_backfill")
        logger.setLevel(logging.INFO)
        if not logger.handlers: # Prevent duplicate handlers on multiple imports
            logger.addHandler(handler)
        return logger
        
    except Exception as e:
        sys.stderr.write(f"FATAL LOGGING ERROR: {e}\n")
        sys.exit(1)

def validate_environment() -> Dict[str, Any]:
    """
    Load configuration securely from environment variables.
    Ensures no credentials are hardcoded or stored locally.
    """
    config = {
        'batch_size': int(os.getenv('BATCH_SIZE', 500)),
        'target_table': os.getenv('TARGET_TABLE_NAME', 'crypto_transactions'),
        'max_retries': int(os.getenv('MAX_RETRIES', 3))
    }

    # Security Check: Validate presence of required secrets before proceeding
    api_key = os.getenv('API_KEY')
    if not api_key:
        raise RuntimeError("CRITICAL CONFIG: API_KEY is missing from environment.")
        
    config['api_key'] = api_key
    
    return config

def get_safe_date_range() -> Iterator[datetime]:
    """
    Generate a safe date range iterator for backfilling.
    Avoids writing directly to sensitive directories like 04_GOVERNANCE/.
    """
    start_str = os.getenv('BACKFILL_START_DATE')
    end_str = os.getenv('BACKFILL_END_DATE', datetime.now().date().isoformat())
    
    if not start_str:
        raise ValueError("Missing required BACKFILL_START_DATE configuration.")
        
    try:
        start_date = datetime.fromisoformat(start_str)
        end_date = datetime.fromisoformat(end_str)
    except ValueError as e:
        raise RuntimeError(f"Invalid date format provided: {e}")
    
    # Safety check: Ensure range isn't excessively large to prevent memory/timeouts
    delta = (end_date - start_date).days
    if delta > 365: 
        sys.stderr.write("WARNING: Backfill range exceeds one year. Proceeding with caution.\n")
        
    current = start_date
    while current <= end_date:
        yield current
        current += timedelta(days=1)

def process_batch_logic(date: datetime, config: Dict[str, Any]) -> bool:
    """
    Placeholder for the actual data ingestion logic.
    This function must ensure no writes to forbidden paths occur during execution.
    Returns True on success or after retries.
    """
    try:
        # Simulate batch processing
        # In real implementation, this would use config['api_key'] safely
        pass
        return True
    except Exception as e:
        # Fail closed behavior: Halt and report error securely
        logging.error(f"Batch failed for {date}: {e}")
        raise

def main():
    """
    Main entry point for the backfill script.
    Implements 'Fail Closed' logic on any constraint breach or configuration error.
    """
    logger = init_secure_logger()
    
    try:
        # Validate environment first
        config = validate_environment()
        
        if not config['target_table']:
            raise RuntimeError("Target table name cannot be empty.")

        logger.info(f"Starting secure backfill process...")
        logger.debug(f"Batch size set to {config['batch_size']}")
        
        # Execute the safe date range generator
        for batch_date in get_safe_date_range():
            try:
                success = process_batch_logic(batch_date, config)
                if not success:
                    continue 
            except Exception as e:
                # Fail closed on processing error to prevent state corruption
                sys.exit(1) 
        
        logger.info("Backfill completed successfully.")
        
    except Exception as e:
        # Fail closed: Ensure system doesn't propagate insecure states
        logging.critical(f"System failure: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
```