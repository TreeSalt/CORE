MISSION: OPSEC_RAG_SCOUT Implementation
DOMAIN: 01_DATA_INGESTION
TYPE: IMPLEMENTATION
VERSION: 1.0

Implement the OPSEC_RAG_SCOUT for the 01_DATA_INGESTION domain.

REQUIREMENTS:
- Implement IntelligenceSource enum (NEWS, MACRO, REGIME, SENTIMENT)
- Implement RagContextPacket dataclass with fields:
    source: IntelligenceSource
    timestamp: str (ISO format)
    payload: dict
    authenticated: bool
    anomaly_detected: bool
- Implement ScoutAdapter abstract base class with:
    fetch() -> RagContextPacket
    validate(packet: RagContextPacket) -> bool
- Implement OpsecRagScout class with:
    __init__(adapters: list[ScoutAdapter], error_ledger_path: str = None)
    query(source: IntelligenceSource) -> RagContextPacket
    _detect_anomaly(packet: RagContextPacket) -> bool
    _sever_feed(adapter: ScoutAdapter, reason: str) -> None (logs to ERROR_LEDGER)
- Anomaly detection: flag packets where payload is empty, timestamp is missing,
  or authenticated=False
- FAIL-CLOSED: if all adapters severed, raise RuntimeError with clear message
- Use only stdlib (no external dependencies)

CONSTRAINTS:
- No hardcoded credentials
- No writes to 04_GOVERNANCE/
- Output valid Python only — no markdown prose
- All classes must be importable and independently testable
