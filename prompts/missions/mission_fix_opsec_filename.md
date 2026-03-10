MISSION: Fix opsec_rag_scout filename drift — Priority 0 Substrate Integrity
DOMAIN: 01_DATA_INGESTION
TYPE: IMPLEMENTATION
VERSION: 1.0
PRIORITY: 0 — ANDON CORD ACTIVE

CONSTITUTIONAL BASIS: Article VI.2 — Substrate Integrity Violation
VIOLATION: opsec_rag_scout.py was ratified and deployed but landed as
           01_DATA_INGESTION/data_ingestion/websocket_handler.py
           This breaks the forensic trail. An auditor reading websocket_handler.py
           will find OpsecRagScout logic. This is a naming/location drift.

ACTION REQUIRED:
1. Create 01_DATA_INGESTION/data_ingestion/opsec_rag_scout.py
   - Copy the OpsecRagScout class, ScoutAdapter ABC, RagContextPacket dataclass,
     and IntelligenceSource enum from websocket_handler.py
   - This is the canonical home for this module

2. Refactor 01_DATA_INGESTION/data_ingestion/websocket_handler.py
   - Remove OpsecRagScout, ScoutAdapter, RagContextPacket, IntelligenceSource
   - websocket_handler.py must contain ONLY WebSocket connection logic
   - If websocket_handler.py is now empty or trivial, reduce to a stub with
     a comment: "WebSocket transport layer — see data_multiplexer.py"

3. Update 01_DATA_INGESTION/data_ingestion/__init__.py
   - Add: from .opsec_rag_scout import OpsecRagScout, ScoutAdapter, RagContextPacket, IntelligenceSource
   - Ensure websocket_handler imports still resolve if anything depends on them

4. Output the complete file for opsec_rag_scout.py

INTERFACE CONTRACT (must be preserved exactly):
  - OpsecRagScout.__init__(adapters: list[ScoutAdapter], error_ledger_path: str = None)
  - OpsecRagScout.query(source: IntelligenceSource) -> RagContextPacket
  - OpsecRagScout._detect_anomaly(packet: RagContextPacket) -> bool
  - OpsecRagScout._sever_feed(adapter: ScoutAdapter, reason: str) -> None
  - ScoutAdapter.fetch() -> RagContextPacket  [ABC]
  - ScoutAdapter.validate(packet: RagContextPacket) -> bool  [ABC]
  - IntelligenceSource: Enum with NEWS, MACRO, REGIME, SENTIMENT
  - RagContextPacket: dataclass with source, timestamp, payload, authenticated, anomaly_detected

CONSTRAINTS:
- stdlib only
- No hardcoded credentials
- No writes to 04_GOVERNANCE/
- All classes must be importable from opsec_rag_scout directly
- Output complete files for both opsec_rag_scout.py and the cleaned websocket_handler.py
