MISSION: Implement RiskManager
DOMAIN: 02_RISK_MANAGEMENT
TYPE: IMPLEMENTATION
VERSION: 1.0

CONTEXT — WHAT ALREADY EXISTS:
The following production modules are already live and must be compatible:
- 01_DATA_INGESTION/data_ingestion/data_multiplexer.py
  - DataMultiplexer, FeederAdapter, WebSocketFeederAdapter
  - NormalizationLayer, QueueSystem, AuthenticationLayer
- 00_PHYSICS_ENGINE/physics_engine/physics_engine.py

REQUIREMENTS:
Implement RiskManager class in 02_RISK_MANAGEMENT/risk_management/risk_manager.py

The class ALREADY EXISTS as a stub. Enhance it to:
- enforce per-trade loss limits (max_trade_loss param)
- enforce daily loss limits (max_daily_loss param)
- read from position ledger BEFORE any position action (constitutional requirement)
- flag trades with risk_disclosure_required=True when estimated_loss > 50% of max_trade_loss
- reject trades that would breach CHECKPOINTS.yaml CP1 limits
- log ALL limit breaches to ERROR_LEDGER format
- FAIL-CLOSED: raise RiskViolationError on any constraint breach

CHECKPOINTS.yaml CP1 limits to enforce:
- max_drawdown_pct: 15.0
- Dead Man's Switch integration: call scripts/dead_mans_switch.py --check on every trade

INTERFACE CONTRACT (other modules depend on this):
- approve_trade(instrument: str, quantity: float, estimated_loss: float) -> bool
- record_loss(amount: float) -> None
- reset_daily_loss() -> None
- get_daily_loss() -> float
- get_position_ledger() -> dict

CONSTRAINTS:
- stdlib only — no external dependencies
- No hardcoded credentials
- No writes to 04_GOVERNANCE/
- All classes must be importable
- RiskViolationError must be importable from this module
