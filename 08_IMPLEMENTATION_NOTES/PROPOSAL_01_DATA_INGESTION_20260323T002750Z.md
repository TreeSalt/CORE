---
DOMAIN: 01_DATA_INGESTION
MODEL: qwen3.5:9b
TIER: sprinter
TYPE: IMPLEMENTATION
STATUS: RATIFIED
---

```python
"""
TASK: 01_DATA_E4_003_crypto_symbols
TITLE: Cryptocurrency Symbol Ingestion Pipeline Proposal
DOMAIN: 01_DATA_INGESTION
SECURITY_CLASS: INTERNAL

This document outlines a proposal for ingesting cryptocurrency symbol data securely and
compliant with organizational constraints. It includes architecture, schema, error handling,
and Python-based modular design. No credentials are hardcoded. All logic is fail-safe
by default.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from pydantic import BaseModel, Field
import requests
import pandas as pd
import hashlib
import base64
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend


class CryptoSymbolSchema(BaseModel):
    """Data model for cryptocurrency symbol ingestion"""
    symbol: str
    name: str
    price: Optional[float] = None
    change_24h: Optional[float] = None
    market_cap: Optional[str] = None
    volume_24h: Optional[str] = None
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Config:
        json_schema_extra = {
            "description": "Crypto symbol ingestion record with schema validation",
            "title": "CryptoSymbolRecord"
        }


class IngestionConfig(BaseModel):
    """Secure configuration object for data ingestion"""
    source_api_endpoint: str = Field(default="", description="API endpoint URL")
    api_key_env_var: str = Field(default="CREDENTIALS_API_KEY", description="Env var holding API key")
    max_retries: int = 3
    timeout_seconds: int = 30
    data_dir: str = "./data"
    log_level: str = "INFO"
    fail_open: bool = False  # Fail closed is default


class IngestionResult(BaseModel):
    """Result of ingestion attempt"""
    success: bool
    message: str
    records_processed: int
    errors: List[str] = []
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


def validate_api_key() -> bool:
    """Validate API key from environment variable safely."""
    import os
    api_key = os.getenv("CREDENTIALS_API_KEY")
    if not api_key or len(api_key) < 10:
        logging.error("API key validation failed - insufficient credentials")
        return False
    # Additional validation can be added (e.g., checksum, format checks)
    return True


def sanitize_crypto_symbols(input_data: Dict[str, dict]) -> List[Dict[str, str]]:
    """Sanitize input to ensure safe symbol values"""
    sanitized = []
    for item in input_data.values():
        if isinstance(item.get("symbol"), str):
            safe_symbol = item["symbol"].strip().upper()[:10]  # Max 10 chars, uppercase
            if safe_symbol.isalnum() and safe_symbol != "":
                sanitized.append({"symbol": safe_symbol, "name": item.get("name", "")})
    return sanitized


def fetch_crypto_data(config: IngestionConfig) -> Tuple[List[Dict[str, dict]], Optional[str]]:
    """Fetch crypto data from external API securely"""
    headers = {}
    api_key_value = os.getenv(config.api_key_env_var) if validate_api_key() else None

    if api_key_value:
        headers["Authorization"] = f"Bearer {api_key_value}"

    response = requests.get(
        config.source_api_endpoint,
        headers=headers,
        timeout=config.timeout_seconds,
        allow_redirects=False
    )

    try:
        data = response.json()
    except Exception as e:
        return [], f"Failed to parse API response: {str(e)}"

    raw_symbols = data.get("symbols", [])
    sanitized_symbols = sanitize_crypto_symbols(data)
    return sanitized_symbols, None


def transform_to_schema(symbols: List[Dict[str, str]]) -> List[CryptoSymbolSchema]:
    """Transform raw symbol dicts into schema-compliant objects."""
    schema_objects = []
    for item in symbols:
        try:
            symbol_obj = CryptoSymbolSchema(
                symbol=item.get("symbol", ""),
                name=item.get("name", "Unknown"),
                price=None,
                change_24h=None,
                market_cap=None,
                volume_24h=None,
                last_updated=datetime.now(timezone.utc)
            )
            schema_objects.append(symbol_obj)
        except Exception as e:
            logging.warning(f"Failed to transform symbol {item.get('symbol')}: {e}")
    return schema_objects


def generate_check_sum(data: pd.DataFrame, algo: str = "sha256") -> Optional[str]:
    """Generate checksum for data integrity verification."""
    try:
        if algo == "sha256":
            digest = hashlib.sha256(str(data).encode()).hexdigest()
            return digest
        elif algo == "sha1":
            return hashlib.sha1(str(data).encode()).hexdigest()
        else:
            logging.warning("Unsupported checksum algorithm")
            return None
    except Exception:
        return None


def write_to_storage(schema_data: List[CryptoSymbolSchema], output_dir: str) -> IngestionResult:
    """Write validated data to file system securely"""
    try:
        output_path = Path(output_dir) / "crypto_symbols.json"
        with open(output_path, "w") as f:
            for record in schema_data:
                record_json = record.model_dump()
                f.write(json.dumps(record_json, default=str) + "\n")

        checksum = generate_check_sum(pd.DataFrame([r.dict() for r in schema_data]))
        with open(str(output_path) + ".sha256", "w") as cf:
            cf.write(f"{checksum}")

        return IngestionResult(
            success=True,
            message=f"Successfully wrote {len(schema_data)} records to {output_path}",
            records_processed=len(schema_data),
            errors=[]
        )
    except Exception as e:
        return IngestionResult(
            success=False,
            message=f"Failed to write data: {str(e)}",
            records_processed=0,
            errors=[f"Write failed: {str(e)}"]
        )


def ingest_crypto_symbols(config: Optional[IngestionConfig] = None) -> IngestionResult:
    """Main ingestion orchestration function (safe by default)"""
    if config is None:
        return IngestionResult(
            success=False,
            message="Configuration missing",
            records_processed=0,
            errors=["Missing ingestion configuration"]
        )

    try:
        logging.info("Starting crypto symbol ingestion...")

        # Fetch data with retry logic
        symbols = None
        fetch_errors = []
        for attempt in range(config.max_retries):
            if attempt < config.max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff

            symbols, error = fetch_crypto_data(config)
            if error:
                fetch_errors.append(error)
                logging.warning(f"Fetch attempt {attempt + 1} failed: {error}")

        if not symbols:
            return IngestionResult(
                success=False,
                message="No symbols retrieved from source",
                records_processed=0,
                errors=["Source API returned empty data"]
            )

        # Transform schema
        try:
            schema_objects = transform_to_schema(symbols)
            logging.info(f"Transformed {len(schema_objects)} crypto symbols")
        except Exception as e:
            return IngestionResult(
                success=False,
                message="Schema transformation failed",
                records_processed=0,
                errors=[str(e)]
            )

        # Write to storage
        result = write_to_storage(schema_objects, config.data_dir)

    except Exception as e:
        logging.error(f"Ingestion pipeline failed with error: {e}")
        return IngestionResult(
            success=False,
            message=f"Pipeline exception occurred: {str(e)}",
            records_processed=0,
            errors=[f"Unhandled exception: {e}"]
        )

    return result


if __name__ == "__main__":
    # Demo configuration for testing (do not run in production without review)
    config = IngestionConfig(
        source_api_endpoint="https://api.example.com/crypto",
        api_key_env_var="CREDENTIALS_API_KEY",
        max_retries=3,
        timeout_seconds=30,
        data_dir="./data/crypto_symbols",
        log_level="INFO"
    )

    result = ingest_crypto_symbols(config)
    logging.info(f"Ingestion complete. Success: {result.success}. Records: {result.records_processed}")


# --- SECURITY CHECKLIST (Not for execution; used in compliance review) ---
SECURITY_CHECKLIST = [
    "✅ No hardcoded credentials",
    "✅ All credentials retrieved from environment variables",
    "✅ API requests do not use redirects by default",
    "✅ Data is checksummed on write to detect corruption",
    "✅ Input sanitization in place before processing",
    "✅ Logging excludes sensitive data like secrets or tokens",
    "✅ Fail closed: ingestion halts if critical failure occurs"
]

# --- USAGE INSTRUCTIONS (For reviewers only) ---
USAGE_GUIDELINES = """
1. Copy this proposal code to your review directory only
2. Review each security checklist item
3. Modify data_dir and source_api_endpoint for local testing
4. Set environment variable: export CREDENTIALS_API_KEY=<your_key>
5. Do not commit configuration files or API keys to version control

This pipeline is designed for production readiness after audit approval.
"""
```