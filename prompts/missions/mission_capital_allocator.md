# MISSION: Capital Allocator — Multi-Strategy Splitter
DOMAIN: 02_RISK_MANAGEMENT
TASK: implement_capital_allocator
TYPE: IMPLEMENTATION
VERSION: 1.0

## CONTEXT — GEMINI STRATEGIC SUGGESTION
When multiple strategies survive the Predatory Gate and enter paper trading
simultaneously, the system needs to decide how to split the $2,000 baseline
across competing strategies without violating MES integer-lot physics
($5/tick, 1 contract minimum).

## BLUEPRINT
Create a CapitalAllocator class that:
1. Reads state/predatory_gate_survivors.json for active strategies
2. Reads state/champion_registry.json for performance metrics
3. Allocates capital based on risk-adjusted ranking:
   - Equal weight: split evenly (baseline approach)
   - Sharpe-weighted: allocate proportional to rolling Sharpe
   - Inverse-volatility: more capital to lower-vol strategies
4. Enforces integer-lot constraint: MES = 1 contract minimum
   - With $2,000 and 1-contract minimum, max 2 concurrent strategies
   - If 3+ survivors, allocator ranks and selects top N
5. Rebalances daily based on updated Champion Registry metrics
6. Writes allocation decisions to state/capital_allocation.json
7. Risk manager must approve all allocations before execution

## DELIVERABLE
File: 02_RISK_MANAGEMENT/risk_management/capital_allocator.py

## CONSTRAINTS
- Total allocation must never exceed CHECKPOINTS.yaml capital limit
- Integer lots only (no fractional MES contracts)
- Fail closed if Risk Manager rejects allocation
- No external API calls
- Output valid Python only
