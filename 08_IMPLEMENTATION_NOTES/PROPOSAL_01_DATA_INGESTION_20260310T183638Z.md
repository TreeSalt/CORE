---
DOMAIN: 01_DATA_INGESTION
MODEL: qwen2.5-coder:32b
TIER: heavy
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

### opsec_rag_scout.py

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

class IntelligenceSource(Enum):
    NEWS = "NEWS"
    MACRO = "MACRO"
    REGIME = "REGIME"
    SENTIMENT = "SENTIMENT"

@dataclass
class RagContextPacket:
    source: IntelligenceSource
    timestamp: str
    payload: str
    authenticated: bool
    anomaly_detected: bool

class ScoutAdapter(ABC):
    @abstractmethod
    def fetch(self) -> RagContextPacket:
        pass

    @abstractmethod
    def validate(self, packet: RagContextPacket) -> bool:
        pass

class OpsecRagScout:
    def __init__(self, adapters: list[ScoutAdapter], error_ledger_path: str = None):
        self.adapters = adapters
        self.error_ledger_path = error_ledger_path

    def query(self, source: IntelligenceSource) -> RagContextPacket:
        for adapter in self.adapters:
            packet = adapter.fetch()
            if packet.source == source:
                if self._detect_anomaly(packet):
                    packet.anomaly_detected = True
                    self._sever_feed(adapter, "Anomaly detected")
                return packet
        raise ValueError(f"No data found for source: {source}")

    def _detect_anomaly(self, packet: RagContextPacket) -> bool:
        # Placeholder for anomaly detection logic
        return False

    def _sever_feed(self, adapter: ScoutAdapter, reason: str) -> None:
        # Placeholder for severing feed logic
        print(f"Severing feed for {adapter} due to: {reason}")
```

### websocket_handler.py

```python
# WebSocket transport layer — see data_multiplexer.py
```

### Update to `__init__.py`

Ensure the following lines are added to `01_DATA_INGESTION/data_ingestion/__init__.py`:

```python
from .opsec_rag_scout import OpsecRagScout, ScoutAdapter, RagContextPacket, IntelligenceSource
```

This refactoring ensures that the `opsec_rag_scout.py` file contains the canonical definitions of `OpsecRagScout`, `ScoutAdapter`, `RagContextPacket`, and `IntelligenceSource`. The `websocket_handler.py` file is cleaned to contain only WebSocket connection logic, and if it is now trivial, it is reduced to a stub with a comment pointing to `data_multiplexer.py`. The `__init__.py` file is updated to ensure proper imports.