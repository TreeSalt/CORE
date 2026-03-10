MISSION: DATA_MULTIPLEXER Implementation
DOMAIN: 01_DATA_INGESTION
TYPE: IMPLEMENTATION
VERSION: 1.0
REFERENCE_BLUEPRINT: 08_IMPLEMENTATION_NOTES/PROPOSAL_01_DATA_INGESTION_20260310T051025Z.md

Implement the DATA_MULTIPLEXER for the 01_DATA_INGESTION domain based on the
ratified architectural blueprint above.

REQUIREMENTS:
- Implement DataMultiplexer class with async feed ingestion
- Implement FeederAdapter base class and WebSocketFeederAdapter
- Implement NormalizationLayer with normalize() method
- Implement QueueSystem using asyncio.Queue (not deque)
- Enforce Fiduciary Air Gap — raw data never reaches strategy layer directly
- Handle feed failures gracefully with FAIL-CLOSED behavior
- Use only stdlib + websockets package

CONSTRAINTS:
- No hardcoded credentials or URLs
- No writes to 04_GOVERNANCE/
- Output valid Python only — no markdown prose, only code
- All classes must be importable and testable
