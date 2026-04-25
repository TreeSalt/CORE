---
DOMAIN: 03_ORCHESTRATION
MODEL: qwen3.5:9b
TIER: cruiser
TYPE: ARCHITECTURE
STATUS: PENDING_REVIEW
---

BRIEF_PREFLIGHT_V5 = """
---
**Brief:** Preflight Runner v5 (E16-01)
**Version:** 0.5.1
**Status:** Final / Production
**Author:** E14.M1 Team

## Purpose
Execute pre-flight validation checks before mission execution starts. Ensures system integrity, dependency availability, and data freshness. Implements strict "anti-hallucination" protocols: no fabrication of plan details unless explicitly stored in the `mission_cache`.

## Exact Imports
```python
import sys
import os
import json
from datetime import datetime
from pathlib import Path
import hashlib
# External dependencies (pinned):
#   - validators>=0.23.1
#   - requests>=2.31.0
#   - pydantic>=2.5.0
```

## Interface Contract
### Class: `PreflightRunner`

**Attributes:**
- `mission_spec`: `Path` to the mission specification file (JSON).
- `environment_status`: `dict[str, str]` Status of system components (e.g., "online", "degraded").
- `dependencies`: `list[DependencyCheckResult]` Results of dependency verification.
- `data_sources`: `list[DataSourceConfig]` Configurations for data feeds (validated against schema).

**Methods:**
1.  **`verify_schema(spec_path: Path)` -> `bool`**: Loads and validates the mission spec JSON against XSD schemas defined in `mission_schemas/`.
2.  **`check_dependency_health()` -> `dict[str, str]`**: Pings dependency endpoints or checks local module imports (using `importlib`).
3.  **`validate_data_sources()` -> `list[ValidationError]`**: Ensures configured data sources have valid URLs/API keys and return expected schema samples.
4.  **`generate_preflight_report()` -> `str`**: Generates a Markdown summary of the validation results.
5.  **`run_preflight_checks()` -> `PreflightResult`**: Orchestrates all checks above. Returns `True` if all pass, raises `MissionHalteredException` if not.

## Implementation Logic
The class `PreflightRunner` must be instantiated with a `Path` to the mission spec.
-   **Schema Validation**: Use `jsonschema.validate()` (or equivalent).
-   **Dependency Check**: Iterate over pinned versions in `requirements.txt`. Verify installation status using `pip show -f <pkg>`. If missing, abort.
-   **Anti-Hallucination**: If a step requires specific data not found in the spec, raise an error referencing the specific schema field. Do *not* invent data or "guess" values.

## Constraints & Guardrails
1.  **No External Calls**: Do not allow external DNS lookups or calls to untrusted endpoints during the preflight phase unless whitelisted.
2.  **Error Handling**: Catch `ImportError`, `ConnectionError`, `ValueError`. Log full stack traces to `logs/preflight_errors.log`.
3.  **Timeouts**: Enforce a 30-second timeout on all network requests (e.g., `requests.get(..., timeout=30)`).

## Testing Requirements
-   **Unit Tests**: Mocked inputs for dependency checks (valid/invalid JSON responses).
-   **Integration Test**: Run against a known working mission spec (E15-Stable).
-   **Coverage**: Ensure 100% coverage of the `PreflightRunner` class methods.

## Amendment Notes
> [AMENDMENT NOTE: E14-Preflight-Gate] - v5 includes strict pinning on external dependencies to mitigate CVEs. Any dependency update must pass a security audit before deployment.
"""

BRIEF_TIER_LOADER_DATA_CLASSES_V5 = """
---
**Brief:** Tier Loader v5 (Dataclasses) (E16-02)
**Version:** 0.5.1
**Status:** Final / Production
**Author:** E14.M1 Team

## Purpose
Refactor the legacy `dict`/`json` based loading logic into typed data classes (using Pydantic or stdlib `dataclasses`). This ensures type safety, validation on load, and better IDE support. Splits logic between "Loader" (parsing) and "Selector" (filtering).

## Exact Imports
```python
import json
from datetime import datetime
from enum import Enum
# External dependencies:
#   - pydantic>=2.5.0
#   - typing_extensions>=4.9.0
#   - fastapi>=0.103.0 (for schemas)
```

## Interface Contract
### Data Classes: `TierData`, `MissionStatus`
-   **`tier_level`: Enum` (e.g., L1, L2, L3)`**
-   **`data_payload`: dict` or `Any` (validated against schema)**
-   **`timestamp`: datetime`**
-   **`metadata`: dict`**

### Class: `TierDataLoader`
**Attributes:**
-   `schema_registry`: `dict[str, Any]` Mapping tier levels to their Pydantic models.

**Methods:**
1.  **`load_tier(tier_level: TierLevel)` -> `ModelType`**: Loads data from storage (DB/JSON) and validates against `schema_registry`. Raises `ValidationError` if schema mismatch.
2.  **`parse_json(raw_data: str, tier: TierLevel)` -> `ModelType`**: Converts raw string to model instance.
3.  **`validate_payload(payload: Any)` -> `bool`**: Checks if payload matches the registered schema for the requested tier.

### Class: `TierSelector`
**Attributes:**
-   `active_tiers`: `set[TierLevel]` List of tiers currently allowed for execution.

**Methods:**
1.  **`select_tiers()` -> `list[TierLevel]`**: Returns subset of active tiers based on mission config (e.g., only L1 for low-res missions).
2.  **`filter_by_criteria(criteria: Criteria)` -> `list[ModelType]`**: Applies business logic filters on the loaded tier data.

## Implementation Logic
-   Use Pydantic V2 models (`BaseModel`). Enable validation on load.
-   Implement JSON schemas for each tier (L1, L2, L3) in `schemas/tier_schema.json`.
-   Ensure `timestamp` is parsed to ISO8601 format strictly.
-   Handle nested objects recursively using Pydantic's `Field(default=None)`.

## Constraints & Guardrails
1.  **No Dynamic Schema Loading**: Do not load schemas from untrusted sources. Use `importlib.resources.files('schemas')` for packaged resources only.
2.  **Validation Errors**: Catch `pydantic.ValidationError` and re-raise as custom domain exception `SchemaMismatchError`.
3.  **Logging**: Log validation failures with the specific field path causing the error (`model_dump()` output included).

## Testing Requirements
-   **Unit Tests**: Create payloads that intentionally violate schema constraints (null fields, wrong types). Verify errors are raised correctly.
-   **Integration Test**: Run `load_tier` against a valid fixture file.
-   **Coverage**: Ensure 95%+ coverage for Pydantic models and loader methods.

## Amendment Notes
> [AMENDMENT NOTE: E14-DT-Split] - v5 explicitly splits parsing logic (`TierDataLoader`) from business logic filtering (`TierSelector`) to reduce coupling. All dataclasses must inherit from `BaseModel`.
"""

BRIEF_TIER_LOADER_SELECTORS_V5 = """
---
**Brief:** Tier Loader v5 (Selectors) (E16-03)
**Version:** 0.5.1
**Status:** Final / Production
**Author:** E14.M1 Team

## Purpose
Implements logic for selecting specific data tiers based on mission context. Replaces procedural "if/else" chains with configurable selector patterns. Supports dynamic filter injection at runtime (e.g., `filter_by_region`, `filter_by_date`).

## Exact Imports
```python
import re
from datetime import datetime
from typing import Protocol, Callable
# External dependencies:
#   - sqlalchemy>=2.0.23 (for DB queries)
#   - fastapi>=0.103.0 (for request context)
```

## Interface Contract
### Class: `TierSelector`
**Attributes:**
-   `filters`: `dict[str, FilterFunction]` Map of filter keys to functions.
-   `active_pattern`: `str` Regex pattern for tier selection.

**Methods:**
1.  **`apply_filter(tier_data: ModelType)` -> `Optional[ModelType]`**: Executes the stored filters against the data class instance.
2.  **`register_filter(key: str, func: Callable)` -> `None`**: Registers a new filter function (e.g., for geo-fencing).
3.  **`select_by_pattern(pattern: str)` -> `bool`**: Checks if a tier's metadata matches the regex pattern (for L1/L2 routing).

## Implementation Logic
-   Define a Protocol `FilterFunction(data: ModelType) -> bool`.
-   Use decorators or dependency injection to register filters (e.g., `@selector.register('region')`).
-   Ensure `select_by_pattern` uses compiled regex objects for performance.
-   Handle `AttributeError` if data fields are missing during filter execution.

## Constraints & Guardrails
1.  **No External Logic**: Filter functions must be local or imported from trusted modules. Do not execute arbitrary user-provided code strings (eval).
2.  **Performance**: Caching active filters is encouraged for high-throughput missions.
3.  **Error Handling**: If a filter raises an exception, log it and skip the tier (fail-open behavior vs fail-closed depending on config).

## Testing Requirements
-   **Unit Tests**: Register dummy filter functions. Test that `apply_filter` correctly filters out non-matching tiers.
-   **Stress Test**: Apply 10k filters against a large dataset. Monitor GC pressure.
-   **Security**: Ensure no `__class__` or `__subclasses__` magic is exposed in filter handlers.

## Amendment Notes
> [AMENDMENT NOTE: E14-SEL-Dyn] - v5 introduces the `FilterFunction` protocol to allow dynamic registration of filters without recompiling. This supports runtime reconfiguration of mission parameters.
"""

BRIEF_TIER_LOADER_SELECTORS_V6 = """
---
**Brief:** Tier Loader v6 (Selectors) - Refinement (E16-04)
**Version:** 0.5.2
**Status:** Alpha / In Review
**Author:** E14.M1 Team

## Purpose
Refine the `TierSelector` logic to handle concurrent filtering scenarios. Introduce atomic updates for filter sets during runtime. Add support for "soft failures" where a tier can pass with warnings rather than hard errors.

## Exact Imports
```python
import asyncio
from concurrent.futures import ThreadPoolExecutor
# ... (same as V5)
```

## Interface Contract
### Class: `TierSelectorAsync` (Extension of TierSelector)
**Attributes:**
-   `lock`: `asyncio.Lock` Ensures thread-safe filter registration.
-   `filter_queue`: `async.Queue` Queue for batch filtering tasks.

**Methods:**
1.  **`async apply_filter_batch(data_set: list[ModelType])` -> `list[ModelType]`**: Asynchronously applies all registered filters to a batch of data using `ThreadPoolExecutor`.
2.  **`register_soft_filter(key: str, func: Callable)` -> `bool`**: Registers a filter that raises warnings instead of errors (`fail_open`).
3.  **`update_filters()` -> `None`**: Atomically updates the active filter set.

## Implementation Logic
-   Implement `apply_filter_batch` using `asyncio.gather`.
-   Use `@contextlib.contextmanager` for the lock to manage concurrency.
-   Handle `concurrent.futures.TimeoutError` by breaking the batch and logging partial results.

## Constraints & Guardrails
1.  **Concurrency Limits**: Do not exceed 20 concurrent filter executions per mission instance to avoid CPU starvation.
2.  **Thread Safety**: Ensure shared state (e.g., active filters) is never modified directly inside a worker thread. Use `Queue` or shared mutable objects protected by locks.
3.  **Memory Leak Prevention**: Explicitly close `ThreadPoolExecutor` when the selector is destroyed.

## Testing Requirements
-   **Concurrency Tests**: Spawn 50 threads trying to register filters simultaneously. Ensure no race conditions.
-   **Batch Test**: Filter a dataset of 10,000 items concurrently. Verify order preservation if needed (or sort after).
-   **Stress Test**: Simulate filter queue back-pressure and ensure graceful degradation.

## Amendment Notes
> [AMENDMENT NOTE: E16-CURR-SYNC] - v6 introduces async support for high-volume filtering tasks, addressing the synchronous bottleneck identified in v5 stress tests.
"""

BRIEF_DATA_INGESTOR_V5 = """
---
**Brief:** Data Ingestor v5 (E16-05)
**Version:** 0.5.1
**Status:** Final / Production
**Author:** E14.M1 Team

## Purpose
Handle incoming raw data streams for ingestion, transformation, and storage. Supports multiple sources: REST APIs, S3 buckets, Kafka topics (mocked), and local file system. Integrates with `PreflightRunner` and `TierDataLoader`.

## Exact Imports
```python
import aiofiles
import asyncio
from typing import AsyncIterator
# External dependencies:
#   - httpx>=0.26.0 (async HTTP client)
#   - aiohttp>=3.9.0
#   - sqlalchemy>=2.0.23
#   - pydantic>=2.5.0
```

## Interface Contract
### Class: `DataIngestor`
**Attributes:**
-   `sources`: `list[DataSourceConfig]` List of configured ingestion endpoints.
-   `buffer_size`: `int` Size of the async buffer (default 100).
-   `storage_engine`: `DatabaseEngine` Instance for writing data.

**Methods:**
1.  **`async ingest_stream(source: DataSourceConfig)` -> `AsyncIterator[ModelType]`**: Reads from source, validates against schema (`TierDataLoader`), and queues for processing.
2.  **`process_batch(batch: list[ModelType])` -> `int`**: Writes batch to DB, returns success count.
3.  **`handle_ingestion_error(error: Exception)` -> `None`**: Logs error, retries if transient (exponential backoff).

## Implementation Logic
-   Use `asyncio.Queue` to buffer incoming data before DB write.
-   Implement `httpx.AsyncClient` with connection pooling for API sources.
-   For S3, use `aiobotocore` or `boto3` asynchronously.
-   Transform raw JSON into Pydantic models (`TierDataLoader.validate_payload`) before storage.
-   Use SQLAlchemy's async engine (`async_session_maker`).

## Constraints & Guardrails
1.  **Rate Limiting**: Enforce rate limits on API sources using `aiohttp.ClientTimeout` and token bucket logic.
2.  **Backpressure**: If buffer is full, pause ingestion (backoff).
3.  **Idempotency**: Ensure write operations are idempotent (handle duplicate IDs gracefully via `upsert`).

## Testing Requirements
-   **Unit Tests**: Mock network calls to simulate slow/down sources. Verify backoff logic.
-   **Integration Test**: Ingest a small dataset from S3 mock and verify DB insertion.
-   **Stress Test**: Simulate burst traffic (1k items/sec) and measure latency/p99.

## Amendment Notes
> [AMENDMENT NOTE: E16-DAT-STRM] - v5 focuses on asynchronous processing pipelines to handle high-throughput ingestion without blocking the main thread. Supports partial write failures for retry logic.
"""

BRIEF_DATA_STORAGE_V5 = """
---
**Brief:** Data Storage v5 (E16-06)
**Version:** 0.5.1
**Status:** Final / Production
**Status:** Alpha / In Review
**Author:** E14.M1 Team

## Purpose
Implements persistence layer for tier data. Supports multiple backends: PostgreSQL, Redis, and local SQLite (for dev). Focuses on ACID compliance, efficient indexing, and query optimization. Integrates with `DataIngestor`.

## Exact Imports
```python
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
import json
# External dependencies:
#   - sqlalchemy>=2.0.23
#   - psycopg2-binary>=2.9.8
#   - redis>=4.6.0
#   - boto3>=1.34.0 (optional)
```

## Interface Contract
### Class: `DataStorage`
**Attributes:**
-   `engine`: `AsyncSession` Instance of the DB engine.
-   `models`: `dict[str, type]` Mapping tier names to SQLAlchemy models.

**Methods:**
1.  **`async store_tier(tier: ModelType)` -> `int`**: Upserts a tier record into the DB. Returns generated ID or version hash.
2.  **`async query_tiers(tier_type: TierLevel, filters: dict)` -> `list[ModelType]`**: Executes optimized queries (indexes used).
3.  **`async archive_old_records(age_days: int)` -> `int`**: Moves old records to a "cold" storage table or deletes if policy set.

## Implementation Logic
-   Use SQLAlchemy async models. Define tables for `L1Data`, `L2Data`, `L3Data`.
-   Add indices on commonly filtered fields (e.g., `timestamp`, `region`).
-   Implement transaction isolation levels (`SERIALIZABLE` for critical writes).
-   For Redis, store hot tier data as JSON with TTL.

## Constraints & Guardrails
1.  **Connection Pooling**: Use `async_with_connection_pool` to manage DB connections efficiently.
2.  **Failover**: If main engine fails, switch to read-only replica or local cache.
3.  **Data Integrity**: Validate input before `UPsert`. Do not allow partial rows (use atomic transactions).

## Testing Requirements
-   **Unit Tests**: Test DB write/read operations with mocked async engine.
persistence layer for tier data. Supports multiple backends: PostgreSQL, Redis, and local SQLite (for dev). Focuses on ACID compliance, efficient indexing, and query optimization. Integrates with `DataIngestor`.

## Exact Imports
```python
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
import json
# External dependencies:
#   - sqlalchemy>=2.0.23
```"