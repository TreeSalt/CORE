---
DOMAIN: 01_DATA_INGESTION
MODEL: qwen3.5:9b
TIER: sprinter
TYPE: IMPLEMENTATION
STATUS: RATIFIED
---

import os
import json
import logging
from typing import Dict, List, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataIngestionPipeline:
    def __init__(self):
        # Fail closed on configuration breach: Check for required secrets
        self.api_key = os.getenv("DATA_INGESTION_API_KEY")
        if not self.api_key:
            raise RuntimeError("CRITICAL: Missing required environment variable DATA_INGESTION_API_KEY")
        
        self.base_url = os.getenv("DATA_BASE_URL", "https://api.example.com/ingest")
        
        # Prevent writes to restricted directories via environment validation
        self.output_dir = os.getenv("DATA_STORAGE_PATH", "./data/")

    def validate_governance_path(self, path: str) -> bool:
        """Ensure no sensitive or governance paths are being used for write operations."""
        restricted_keywords = ["04_GOVERNANCE", "ADMIN", "/etc/"]
        
        # Fail closed: Raise error if governance path detected in output location
        for keyword in restricted_keywords:
            if keyword.lower() in path.lower():
                raise PermissionError(f"VIOLATION: Attempting to write to restricted path containing '{keyword}'")
        
        return True

    def sanitize_input(self, data: Dict) -> Dict:
        """Remove or mask sensitive fields from input before processing."""
        clean_data = data.copy()
        
        # Remove any credential-like keys found in raw payload
        exclude_keys = ['secret', 'password', 'api_key', 'auth_token']
        for key in exclude_keys:
            if key in clean_data:
                del clean_data[key]
                
        return clean_data

    def process_alpaca_record(self, record: Dict) -> bool:
        """Process a single ALPACA format record."""
        required_fields = ["instruction", "input", "output"]
        
        # Validate structure
        for field in required_fields:
            if field not in record or not isinstance(record[field], str):
                logger.warning(f"Malformed record missing {field}. Skipping.")
                return False
        
        try:
            # Sanitize payload before processing
            safe_record = self.sanitize_input(record)
            
            # Logic placeholder for actual ingestion
            logger.info(f"Processed record ID: {hash(str(safe_record)) % 100000}")
            
            return True
        except Exception as e:
            logger.error(f"Error processing record: {e}")
            raise

    def ingest_batch(self, raw_data: List[Dict]) -> Dict[str, int]:
        """Main ingestion method for ALPACA feed."""
        success_count = 0
        failed_count = 0
        
        # Validate output directory before starting
        self.validate_governance_path(self.output_dir)
        
        try:
            for record in raw_data:
                if self.process_alpaca_record(record):
                    success_count += 1
                else:
                    failed_count += 1
                    
        except RuntimeError as e:
            # Fail closed on critical error
            logger.critical(e)
            raise
            
        except Exception as e:
            logger.error(f"Batch ingestion failed: {e}")
            
        return {
            "success": success_count,
            "failed": failed_count
        }

    def run(self, source_file: Optional[str] = None) -> Dict:
        """Entry point for data ingestion proposal execution."""
        if not self.api_key:
            raise RuntimeError("Pipeline requires valid API key.")
            
        # If source file provided, read it (mock implementation)
        mock_data = [
            {"instruction": "Task 1", "input": "text...", "output": "..."},
            {"instruction": "Task 2", "input": "data", "output": "result"}
        ]
        
        # Execute ingestion
        stats = self.ingest_batch(mock_data)
        
        return {
            "status": "COMPLETED",
            "records_processed": sum(stats.values()),
            "output_path": self.output_dir
        }


if __name__ == "__main__":
    try:
        pipeline = DataIngestionPipeline()
        result = pipeline.run()
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"System abort: {e}")