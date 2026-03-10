---
DOMAIN: 01_DATA_INGESTION
MODEL: qwen2.5-coder:32b
TIER: heavy
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

### opsec_rag_scout.py

```python
from enum import Enum
from dataclasses import dataclass
from abc import ABC, abstractmethod

class IntelligenceSource(Enum):
    NEWS = 'news'
    MACRO = 'macro'
    REGIME = 'regime'
    SENTIMENT = 'sentiment'

@dataclass
class RagContextPacket:
    source: IntelligenceSource
    timestamp: str
    payload: dict
    authenticated: bool
    anomaly_detected: bool = False

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
            if packet.source == source and adapter.validate(packet):
                packet.anomaly_detected = self._detect_anomaly(packet)
                return packet
        return None

    def _detect_anomaly(self, packet: RagContextPacket) -> bool:
        # Implement anomaly detection logic here
        return False

    def _sever_feed(self, adapter: ScoutAdapter, reason: str) -> None:
        # Implement feed severing logic here
        pass
```

### websocket_handler.py

```python
# WebSocket transport layer — see data_multiplexer.py

# No WebSocket connection logic in this file as it was moved to data_multiplexer.py
```

### Update to __init__.py

Add the following line to `01_DATA_INGESTION/data_ingestion/__init__.py`:

```python
from .opsec_rag_scout import OpsecRagScout, ScoutAdapter, RagContextPacket, IntelligenceSource
```

This ensures that the necessary classes and modules are importable from the package, preserving the interface contract and addressing the forensic trail issue.