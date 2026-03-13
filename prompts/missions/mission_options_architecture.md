# MISSION: Options Instrument Architecture
DOMAIN: 00_PHYSICS_ENGINE
TASK: design_options_instrument
TYPE: ARCHITECTURE
VERSION: 1.0

## CONTEXT — ROADMAP v3.0 Phase 2+ DELIVERABLE
The current Physics Engine supports futures only (MES). To capture
asymmetric opportunities (moonshots), we need an options instrument
class. Options provide:
- Defined risk: max loss = premium paid
- Asymmetric payoff: unlimited upside on calls, large upside on puts
- Leverage: control large notional with small capital
- Volatility trading: profit from IV expansion regardless of direction

## WHY NOT NOW
Per CHECKPOINTS.yaml, CP1 requires proving the system works on the
simplest possible instrument (MES futures). Options add:
- Greeks (delta/gamma/theta/vega) that change every tick
- Time decay that erodes position value daily
- Implied volatility surfaces that shift with market regime
- Exercise/assignment risk at expiration
- Spread strategies (verticals, straddles, condors)

The constitutional guardrails (max DD, DMS) must be battle-tested
on simple instruments before adding this complexity.

## BLUEPRINT (ARCHITECTURE ONLY)
Design the OptionsInstrumentSpec class:

1. OptionsInstrumentSpec extends InstrumentSpec:
   - underlying: InstrumentSpec (e.g., SPY, MES)
   - strike_price: float
   - expiration: datetime
   - option_type: CALL | PUT
   - contract_multiplier: int (typically 100 for equity options)

2. OptionsGreeks dataclass:
   - delta, gamma, theta, vega, rho
   - iv: implied volatility
   - time_to_expiry: float (years)

3. OptionsPricingEngine:
   - black_scholes(S, K, T, r, sigma) -> price
   - compute_greeks(S, K, T, r, sigma) -> OptionsGreeks
   - iv_from_price(market_price, S, K, T, r) -> float

4. OptionsStrategy interface extends Strategy:
   - prepare_data() returns: entry_signal, exit_signal, ATR,
     PLUS: preferred_strike, preferred_expiry, preferred_type
   - Risk manager validates: max_premium_per_trade, max_total_premium,
     max_theta_decay_per_day

5. Multi-leg support (future):
   - Vertical spreads, straddles, iron condors
   - Each leg is an independent OptionsInstrumentSpec
   - Combined P&L computed at portfolio level

Document as class skeletons with type hints and docstrings.

## DELIVERABLE
File: antigravity_harness/instruments/options_architecture.py

## CONSTRAINTS
- ARCHITECTURE only — class skeletons, not implementation
- Must reference existing InstrumentSpec interface
- Must define how the Risk Manager enforces options-specific limits
- No external API calls
- Output valid Python only
