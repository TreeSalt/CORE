# MISSION: Predatory Gate for E8 Strategies
DOMAIN: 00_PHYSICS_ENGINE
TYPE: IMPLEMENTATION

## DELIVERABLE
File: scripts/run_predatory_gate_e8.py

## REQUIREMENTS
- Run stress test on all E8 strategies (rsi_divergence, market_profile_value, overnight_range_trap, vwap_bands, keltner_squeeze)
- Scenarios: Flash crash (-8% in 5 bars), Gap down (-3% overnight), Whipsaw (5 direction changes in 10 bars), Dead flat (0.1% range for 50 bars)
- Track max drawdown per strategy per scenario
- Kill threshold: 15% max drawdown in any scenario
- Output JSON report to reports/predatory/E8_GATE_{timestamp}.json
- No external API calls
- Output valid Python only
