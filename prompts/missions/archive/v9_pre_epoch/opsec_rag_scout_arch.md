MISSION: OPSEC_RAG_SCOUT Architecture
DOMAIN: 01_DATA_INGESTION
TYPE: ARCHITECTURE
VERSION: 1.0

Design the OPSEC_RAG_SCOUT — a Retrieval-Augmented Intelligence layer for the
01_DATA_INGESTION domain.

PURPOSE:
The OPSEC_RAG_SCOUT sits between raw external data and the strategy layer.
It retrieves relevant market context (news, macro signals, regime indicators)
and packages it into authenticated intelligence payloads. Raw external data
NEVER reaches the strategy layer directly — it must pass through the Scout's
normalization and authentication pipeline first. This is a constitutional
requirement (Fiduciary Air Gap, Article IV.7).

REQUIREMENTS:
- Define ScoutAdapter base interface for pluggable intelligence sources
- Define RagContextPacket dataclass: the authenticated payload handed to strategy layer
- Define OpsecRagScout orchestrator class that:
  - Accepts multiple ScoutAdapters
  - Normalizes and deduplicates intelligence from all sources
  - Detects poisoned/anomalous data (Article IV.7 — SOVEREIGN INGESTION)
  - Severs feed and logs to ERROR_LEDGER on anomaly detection
  - Produces a single authenticated RagContextPacket per query
- Define IntelligenceSource enum: NEWS, MACRO, REGIME, SENTIMENT
- Data flow diagram showing Scout position in the full pipeline:
  External Sources → ScoutAdapters → OpsecRagScout → RagContextPacket → Strategy Layer

CONSTRAINTS:
- No hardcoded credentials or API keys
- No writes to 04_GOVERNANCE/
- Output must be a Markdown architectural blueprint (ARCHITECTURE type)
- No direct asyncio.run() at module level
