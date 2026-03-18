# Mission: core-sdk interfaces.py — Abstract Gate Protocols

## Domain
07_INTEGRATION

## Model Tier
Heavy (27b)

## Description
Create core_sdk/interfaces.py with abstract base classes that define the contracts between CORE and any payload system (like MANTIS).

EXACT INTERFACES:

1. GateProtocol(ABC) — abstract check(proposal: dict) -> GateResult
2. GateResult — passed: bool, reason: str, gate_name: str
3. RunnerProtocol(ABC) — abstract execute(mission: Mission) -> BenchmarkReport
4. AnalyzerProtocol(ABC) — abstract analyze(results: list) -> list[dict]
5. HealthCheckProtocol(ABC) — abstract check() -> HealthStatus

Import types from core_sdk.types (relative import: from .types import ...).
ALL imports from Python stdlib ONLY (abc, typing, dataclasses).
NO external dependencies.

OUTPUT: core_sdk/interfaces.py
TEST: Create a concrete implementation of GateProtocol. Call check(). Assert GateResult returned.
