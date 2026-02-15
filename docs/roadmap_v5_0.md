# Roadmap: v5.0 Event Horizon

# Roadmap: v5.0 Event Horizon

## Phase 0: Reality Gap Measurement (MANDATORY)
**Goal**: Quantify the Simulation-to-Reality deviation.
1.  [ ] **Slippage Auditor**: Compare "Ideal" prices vs "Realized" prices.
2.  [ ] **Latency Impact Analysis**: Measure effect of 50ms-500ms delay.
3.  [ ] **Fill Probability Model**: Replace "Magic Fill" with probabilistic execution based on volume.

## Phase 1: The Quantum Ledger (Options Core)
**Goal**: Enable Derivatives Trading.
1.  [ ] **Data Architecture Upgrade**: Refactor `DataConfig` to support Option Chains (Sym, Type, Strike, Exp).
2.  [ ] **Black-Scholes Engine**: Implement `antigravity_harness.pricing` for theoretical pricing and Greeks.
3.  [ ] **Contract Logic**: Update `PortfolioAccount` to handle Expiration, Assignment, and Exercise events.

## Phase 2: The Reality Engine (High-Fidelity Sim)
**Goal**: "Lowest loss between reality and testing."
1.  [ ] **Order Book Micro-Physics**:
    -   Implement Bid/Ask spread simulation (even if using estimate from Low/Close).
    -   Implement "Liquidity Constraints" (Order size vs Volume).
2.  [ ] **Market Impact Model**:
    -   Square-Root Law implementation (Impact ~ Vol * sqrt(OrderSize / DailyVol)).
3.  [ ] **Slippage Auditor**: A tool to compare "Ideal" vs "Realized" prices in simulation.

## Phase 3: The Oracle (Alpha Generation)
**Goal**: Automated Strategy Improvement.
1.  [ ] **Feature Store**: Standardize inputs for ML models.
2.  [ ] **Optimizer Upgrade**: Move from "Inverse Vol" to MVO (Mean-Variance Optimization) or HRP (Hierarchical Risk Parity).

## Immediate Steps (Next 24 Hours)
1.  **Refactor Engine for Derivatives**: The biggest blocker to options is the assumption that `price` is a single float. Options have `price`, `strike`, `greeks`.
    -   *Action*: Create `Instrument` class abstraction.
2.  **Import Option Data Support**: We need a way to mock or load option chains.

## Success Metrics
-   **Reality Gap**: < 0.05% deviation between Backtest and Paper Trade.
-   **Asset Coverage**: Full support for SPY Options Chain simulations.
-   **Reliability**: 99.9% correct handling of Assignment/Exercise logic.
