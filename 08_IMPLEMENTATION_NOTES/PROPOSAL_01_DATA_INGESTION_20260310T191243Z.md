---
DOMAIN: 01_DATA_INGESTION
MODEL: qwen2.5-coder:32b
TIER: heavy
TYPE: IMPLEMENTATION
STATUS: RATIFIED
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
            if adapter.source == source:
                packet = adapter.fetch()
                if self._detect_anomaly(packet):
                    packet.anomaly_detected = True
                if not adapter.validate(packet):
                    self._sever_feed(adapter, "Validation failed")
                return packet
        raise ValueError(f"No adapter found for source: {source}")

    def _detect_anomaly(self, packet: RagContextPacket) -> bool:
        # Placeholder for anomaly detection logic
        return False

    def _sever_feed(self, adapter: ScoutAdapter, reason: str) -> None:
        # Placeholder for severing feed logic
        print(f"Severing feed for {adapter} due to {reason}")
```

### websocket_handler.py

```python
# WebSocket transport layer — see data_multiplexer.py

# Ensure that if there are any dependencies on the classes that were moved,
# they are redirected to opsec_rag_scout.py
from .opsec_rag_scout import OpsecRagScout, ScoutAdapter, RagContextPacket, IntelligenceSource

# Example of how to use the moved classes
# Note: This is just a placeholder and should be replaced with actual WebSocket logic
# class MyWebSocketHandler:
#     def __init__(self):
#         self.scout = OpsecRagScout(adapters=[])
# 
#     def handle_websocket_message(self, message):
#         # Process WebSocket message
#         pass
```

### __init__.py

```python
from .opsec_rag_scout import OpsecRagScout, ScoutAdapter, RagContextPacket, IntelligenceSource
```

This set of changes ensures that the OpsecRagScout-related classes are properly encapsulated in their own module (`opsec_rag_scout.py`), while the `websocket_handler.py` file is left to handle only WebSocket-related logic. The `__init__.py` file is updated to include the necessary imports to maintain compatibility with any existing code that may depend on these classes.