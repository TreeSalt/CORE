---
DOMAIN: 01_DATA_INGESTION
MODEL: qwen2.5-coder:32b
TIER: heavy
TYPE: IMPLEMENTATION
STATUS: RATIFIED
---

```python
# 01_DATA_INGESTION/data_ingestion/opsec_rag_scout.py

from enum import Enum
from dataclasses import dataclass
from abc import ABC, abstractmethod
import logging
from datetime import datetime

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
    def __init__(self, adapters: list[ScoutAdapter], error_ledger_path: str = None):
        self.adapters = adapters
        self.error_ledger_path = error_ledger_path
        self.logger = logging.getLogger(__name__)

    def query(self, source: IntelligenceSource) -> RagContextPacket:
        for adapter in self.adapters:
            if isinstance(adapter, ScoutAdapter):
                packet = adapter.fetch()
                if packet.source == source:
                    if adapter.validate(packet):
                        packet.anomaly_detected = self._detect_anomaly(packet)
                        if packet.anomaly_detected:
                            self._sever_feed(adapter, "Anomaly detected in the data packet")
                        return packet
        raise RuntimeError("No valid data packet found for the specified source")

    def _detect_anomaly(self, packet: RagContextPacket) -> bool:
        if not packet.payload:
            return True
        if not packet.timestamp or packet.timestamp == "":
            return True
        if not packet.authenticated:
            return True
        return False

    def _sever_feed(self, adapter: ScoutAdapter, reason: str) -> None:
        self.adapters.remove(adapter)
        if self.error_ledger_path:
            with open(self.error_ledger_path, 'a') as ledger:
                ledger.write(f"{datetime.utcnow().isoformat()} - Severed feed for {adapter.__class__.__name__}: {reason}\n")
        if not self.adapters:
            raise RuntimeError("All feeds severed — OpsecRagScout FAIL-CLOSED")
```

### Explanation:
1. **IntelligenceSource (enum)**: Defines the different types of intelligence sources.
2. **RagContextPacket (dataclass)**: Represents the data packet structure with fields for source, timestamp, payload, authentication status, and anomaly detection status.
3. **ScoutAdapter (ABC)**: An abstract base class for adapters that must implement `fetch` and `validate` methods.
4. **OpsecRagScout**: 
   - Initializes with a list of adapters and an optional error ledger path.
   - `query` method fetches data from adapters, validates it, and checks for anomalies.
   - `_detect_anomaly` method checks for specific anomaly rules.
   - `_sever_feed` method removes the adapter from the list and logs the reason if an error ledger path is provided. If all adapters are severed, it raises a `RuntimeError`.

### Constraints:
- Uses only standard library modules.
- No hardcoded credentials or URLs.
- No writes to `04_GOVERNANCE/`.
- All classes are importable independently.
- No `asyncio.run()` at module level.
- Fail-closed on any constraint breach.