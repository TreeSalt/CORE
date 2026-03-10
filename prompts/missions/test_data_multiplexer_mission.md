MISSION: Write test suite for DATA_MULTIPLEXER
DOMAIN: 01_DATA_INGESTION
TYPE: IMPLEMENTATION
VERSION: 1.0

Write a pytest test suite for the DATA_MULTIPLEXER module at:
01_DATA_INGESTION/data_ingestion/data_multiplexer.py

REQUIREMENTS:
- Test file: 06_BENCHMARKING/tests/01_DATA_INGESTION/test_data_multiplexer.py
- Test FeederAdapter is abstract — cannot be instantiated directly
- Test WebSocketFeederAdapter instantiates with a url parameter
- Test NormalizationLayer.normalize() returns dict with symbol, price, timestamp keys
- Test QueueSystem.enqueue() adds to queue
- Test AuthenticationLayer raises on data integrity breach
- Test DataMultiplexer instantiates cleanly
- Use pytest, unittest.mock for async mocking
- All tests must be sync (use pytest-asyncio or mock async methods)
- No real network connections — mock all websocket calls

CONSTRAINTS:
- No hardcoded credentials
- No writes to 04_GOVERNANCE/
- Tests must be runnable with: python3 -m pytest 06_BENCHMARKING/tests/01_DATA_INGESTION/ -v
