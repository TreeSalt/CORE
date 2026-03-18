"""core_sdk.interfaces — Abstract gate and runner protocols."""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from .types import Mission, BenchmarkReport, HealthStatus

@dataclass
class GateResult:
    passed: bool
    reason: str
    gate_name: str

class GateProtocol(ABC):
    @abstractmethod
    def check(self, proposal: dict) -> GateResult: ...

class RunnerProtocol(ABC):
    @abstractmethod
    def execute(self, mission: Mission) -> BenchmarkReport: ...

class AnalyzerProtocol(ABC):
    @abstractmethod
    def analyze(self, results: list) -> list: ...

class HealthCheckProtocol(ABC):
    @abstractmethod
    def check(self) -> HealthStatus: ...
