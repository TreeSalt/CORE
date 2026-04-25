# MISSION: mantis_v2_architecture
TYPE: ARCHITECTURE

## DELIVERABLE
File: docs/architecture/MANTIS_V2_ARCHITECTURE.md

## SCOPE
Architecture document for MANTIS v2 covering:
- Dependency injection pattern (no module-level singletons)
- Pipeline composition: data_provider → regime_detector → trend_signal → position_sizer → executor
- CPCV validation hookups (Combinatorial Purged Cross-Validation, ratified in E12)
- Path A regulatory positioning (software tool, user brings keys)
- Risk circuit breakers: drawdown limits, daily loss caps, position concentration
- Alpha decay monitoring (paper → live, expect ~40% decay)
- BTC/USD as initial paper trading instrument via Alpaca

Existing components to integrate:
- mantis_core/physics/trend_signal.py (deployed in E13)
- mantis_core/risk/position_sizer.py (deployed in E13)
- scripts/mantis_paper_launcher.py (deployed in E13)

## OUTPUT FORMAT
Markdown with component diagrams (text-art), interface contracts,
data flow descriptions, and a phased rollout plan.
