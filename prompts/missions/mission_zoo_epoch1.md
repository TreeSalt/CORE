MISSION: Zoo Epoch 1 — Strategy Variant Architecture Blueprints
DOMAIN: 00_PHYSICS_ENGINE
TYPE: ARCHITECTURE
VERSION: 1.0

SOVEREIGN MANDATE — SELECTION PRESSURE:
Breed for DRAWDOWN RESISTANCE and RISK-ADJUSTED RETURN.
Do NOT optimize for maximum absolute return.
Primary goal: survive the Fiduciary 15% Max Drawdown limit.
Secondary goal: maximize Sharpe/Sortino ratio.
We are breeding unkillable macro-survivors, not fragile sprinters.

INCUMBENT CHAMPION (must be beaten):
- Strategy ID: TEST_1d
- Profit Factor: 2.0
- Status: STAGING
- Timeframe: 1d
- Known weakness: not yet stress-tested for Black Swan events

WHAT TO PRODUCE:
Design 5 strategy variant BLUEPRINTS that will compete against TEST_1d.
Each blueprint must specify:

1. STRATEGY_ID — unique identifier (e.g. ZOO_E1_001)
2. CORE_LOGIC — entry/exit signal topology (indicators, conditions)
3. TIMEFRAME — which timeframe(s) it operates on
4. REGIME_AFFINITY — which macro regime it is designed for
   (trending, mean-reverting, high-vol, low-vol, crisis)
5. DRAWDOWN_DEFENSE — specific mechanism to enforce 15% drawdown ceiling
6. VOLATILITY_DRAG_MITIGATION — how it reduces volatility drag
7. ANTI_FRAGILITY_SCORE — estimated resilience to Black Swan events (1-10)
8. EXPECTED_SHARPE — realistic Sharpe ratio estimate
9. EXPECTED_SORTINO — realistic Sortino ratio estimate
10. GRAVEYARD_AVOIDANCE — what known anti-patterns from GRAVEYARD.md it avoids

GRAVEYARD ANTI-PATTERNS TO AVOID:
- websocket.SSLOpt.CERT_NONE (technical, not strategic — but noted)
- Do not reference this in strategy logic

DIVERSITY REQUIREMENT:
The 5 variants must be architecturally diverse — no two variants should
share the same core signal type. Suggested diversity axes:
- Momentum vs Mean-Reversion
- Trend-following vs Range-bound
- Single-timeframe vs Multi-timeframe
- Indicator-based vs Price-action-based
- Volatility-adaptive vs Fixed-parameter

OUTPUT FORMAT:
Produce a markdown document with all 5 blueprints clearly structured.
Each blueprint should be self-contained and implementable.
End with a SELECTION_CRITERIA section summarizing how the Zoo will
rank these variants after backtesting.

CONSTRAINTS:
- This is ARCHITECTURE — produce markdown blueprints, not Python code
- No hardcoded credentials
- No writes to 04_GOVERNANCE/
- All blueprints must respect PhysicsEngine constraints:
  - allow_fractional_shares=False for MES
  - max_contracts=1 (paper phase)
  - no_overnight=True
  - max_trades_per_day=3
