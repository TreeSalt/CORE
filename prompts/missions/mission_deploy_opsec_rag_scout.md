MISSION: Deploy OPSEC_RAG_SCOUT to production path
DOMAIN: 01_DATA_INGESTION
TYPE: IMPLEMENTATION
VERSION: 1.0

CONTEXT — WHAT ALREADY EXISTS IN PRODUCTION:
- 01_DATA_INGESTION/data_ingestion/data_multiplexer.py
  DataMultiplexer, FeederAdapter, WebSocketFeederAdapter,
  NormalizationLayer, QueueSystem, AuthenticationLayer

REFERENCE — RATIFIED BLUEPRINT:
08_IMPLEMENTATION_NOTES/PROPOSAL_01_DATA_INGESTION_20260310T065628Z.md (ARCHITECTURE)
08_IMPLEMENTATION_NOTES/PROPOSAL_01_DATA_INGESTION_20260310T065306Z.md (IMPLEMENTATION)

REQUIREMENTS:
Write 01_DATA_INGESTION/data_ingestion/opsec_rag_scout.py

Implement the following classes:

1. IntelligenceSource (enum):
   NEWS, MACRO, REGIME, SENTIMENT

2. RagContextPacket (dataclass):
   source: IntelligenceSource
   timestamp: str  # ISO format
   payload: dict
   authenticated: bool
   anomaly_detected: bool

3. ScoutAdapter (ABC):
   fetch() -> RagContextPacket
   validate(packet: RagContextPacket) -> bool

4. OpsecRagScout:
   __init__(adapters: list[ScoutAdapter], error_ledger_path: str = None)
   query(source: IntelligenceSource) -> RagContextPacket
   _detect_anomaly(packet: RagContextPacket) -> bool
   _sever_feed(adapter: ScoutAdapter, reason: str) -> None

ANOMALY DETECTION RULES (constitutional — Fiduciary Air Gap Article IV.7):
- Flag if payload is empty dict
- Flag if timestamp is missing or empty string
- Flag if authenticated=False
- On anomaly: call _sever_feed(), log to ERROR_LEDGER, mark packet anomaly_detected=True
- If ALL adapters severed: raise RuntimeError("All feeds severed — OpsecRagScout FAIL-CLOSED")

INTERFACE CONTRACT (other modules depend on this):
- query() must always return a RagContextPacket — never None
- _sever_feed() must write to error_ledger_path if provided
- Raw external data NEVER reaches caller without going through validate()

CONSTRAINTS:
- stdlib only (enum, dataclasses, abc, logging, datetime)
- No hardcoded credentials or URLs
- No writes to 04_GOVERNANCE/
- All classes must be importable independently
- No asyncio.run() at module level
