# Mission: core-sdk types.py — Shared Dataclasses

## Domain
07_INTEGRATION

## Model Tier
Heavy (27b)

## Description
Create core_sdk/types.py containing shared dataclasses used by both CORE and MANTIS.

EXACT CLASSES TO IMPLEMENT (based on real project usage):

1. Mission — id: str, domain: str, task: str, type: str, status: str, priority: int, authored_by: str, authored_at: str, result: dict|None
2. ProbeSchema — id: str, category: str, prompt: str, expected_behavior: str|None
3. ProbeResult — probe_id: str, model: str, response_text: str, response_length: int, timestamp: str, passed: bool
4. BenchmarkReport — domain: str, task: str, score: float, passed: bool, failures: list[str], timestamp: str
5. SecurityReport — file_path: str, passed: bool, findings: list[dict], scan_type: str
6. HealthStatus — healthy: bool, vram_total: int, vram_used: int, vram_free: int, models_loaded: list[str]
7. DomainConfig — domain_id: str, security: str, model_tier: str, write_path: str

ALL classes must use @dataclass decorator.
ALL must have to_dict() and from_dict() classmethods for JSON serialization.
ALL imports from Python stdlib ONLY (dataclasses, typing, json).
NO external dependencies.

OUTPUT: core_sdk/types.py
Also create core_sdk/__init__.py that imports all classes.
TEST: Instantiate each class, serialize to dict, deserialize back, assert equality.
