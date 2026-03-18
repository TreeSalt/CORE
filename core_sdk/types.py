"""core_sdk.types — Shared dataclasses for CORE and MANTIS."""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Optional
import json

@dataclass
class Mission:
    id: str
    domain: str
    task: str
    type: str
    status: str
    priority: int
    authored_by: str
    authored_at: str
    result: Optional[dict] = None

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> Mission:
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})

@dataclass
class ProbeSchema:
    id: str
    category: str
    prompt: str
    expected_behavior: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> ProbeSchema:
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})

@dataclass
class ProbeResult:
    probe_id: str
    model: str
    response_text: str
    response_length: int
    timestamp: str
    passed: bool

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> ProbeResult:
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})

@dataclass
class BenchmarkReport:
    domain: str
    task: str
    score: float
    passed: bool
    failures: list = field(default_factory=list)
    timestamp: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> BenchmarkReport:
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})

@dataclass
class SecurityReport:
    file_path: str
    passed: bool
    findings: list = field(default_factory=list)
    scan_type: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> SecurityReport:
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})

@dataclass
class HealthStatus:
    healthy: bool
    vram_total: int
    vram_used: int
    vram_free: int
    models_loaded: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> HealthStatus:
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})

@dataclass
class DomainConfig:
    domain_id: str
    security: str
    model_tier: str
    write_path: str

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> DomainConfig:
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})
