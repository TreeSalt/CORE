---
DOMAIN: 01_DATA_INGESTION
MODEL: qwen2.5-coder:32b
TIER: heavy
TYPE: IMPLEMENTATION
STATUS: RATIFIED
---

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List

class IntelligenceSource(Enum):
    NEWS = 'NEWS'
    MACRO = 'MACRO'
    REGIME = 'REGIME'
    SENTIMENT = 'SENTIMENT'

@dataclass
class RagContextPacket:
    source: IntelligenceSource
    timestamp: str  # ISO format
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
    def __init__(self, adapters: List[ScoutAdapter], error_ledger_path: str = None):
        self.adapters = adapters
        self.error_ledger_path = error_ledger_path
        self.active_adapters = adapters.copy()

    def query(self, source: IntelligenceSource) -> RagContextPacket:
        for adapter in self.active_adapters:
            packet = adapter.fetch()
            if packet.source == source:
                if adapter.validate(packet):
                    packet.anomaly_detected = self._detect_anomaly(packet)
                    return packet
                else:
                    self._sever_feed(adapter, "Packet validation failed")
            else:
                self._sever_feed(adapter, "Mismatched source")
        
        if not self.active_adapters:
            raise RuntimeError("All adapters have been severed. No active adapters to query.")
        
        raise RuntimeError(f"No valid packet found for source {source}")

    def _detect_anomaly(self, packet: RagContextPacket) -> bool:
        if not packet.payload or not packet.timestamp or not packet.authenticated:
            return True
        return False

    def _sever_feed(self, adapter: ScoutAdapter, reason: str) -> None:
        if self.error_ledger_path:
            with open(self.error_ledger_path, 'a') as ledger:
                ledger.write(f"Severed adapter {adapter}: {reason}\n")
        self.active_adapters.remove(adapter)
        if not self.active_adapters:
            raise RuntimeError("All adapters have been severed. No active adapters to query.")
```

This code proposal implements the `OpsecRagScout` system as described, using only the standard library. The `IntelligenceSource` enum, `RagContextPacket` dataclass, `ScoutAdapter` abstract base class, and `OpsecRagScout` class are all included, with the specified constraints and requirements applied.