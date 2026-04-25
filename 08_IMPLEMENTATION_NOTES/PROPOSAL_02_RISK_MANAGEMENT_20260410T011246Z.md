---
DOMAIN: 02_RISK_MANAGEMENT
MODEL: qwen3.5:9b
TIER: cruiser
TYPE: ARCHITECTURE
STATUS: PENDING_REVIEW
---

# Mantis Kelly Position Sizer Architecture

## Overview

The Mantis Kelly Position Sizer (`MANTIS_KELLY_POSITION_SIZER`) is a critical component of the Mantis trading system designed to execute position sizing logic using the Kelly Criterion methodology. It integrates with the broader strategy execution framework, specifically interacting with the `StrategyExecution` module and utilizing data from the `DataPipeline`.

## Core Responsibility

1.  **Position Sizing**: Calculate optimal trade sizes based on the Kelly formula.
2.  **Risk Management**: Enforce risk constraints (e.g., max position size % of equity).
3.  **Edge Validation**: Validate that the calculated edge is significant enough to justify a trade.
4.  **Confidence Intervals**: Compute statistical confidence intervals for expected value to reduce overfitting risks.

## Architectural Context

### Dependencies

*   **`StrategyExecution`**: The sizer receives execution context (order requests, market data). It sends back position signals.
*   **`DataPipeline`**: Provides historical and real-time trade data for backtesting or live trading. This includes signals and realized P/L.
*   **`PositionSizerModule`**: Abstract parent class defining the `PositionSizer` interface (`calculate_position()`, `validate_trade()`).

### Interfaces & Contracts

```python
class PositionSizer:
    def calculate_position(self, trade_signal, market_data):
        """Returns a dictionary with 'size', 'direction', and 'confidence'. Raises ValueError if invalid."""
        pass

    def validate_trade(self, edge, volatility):
        """Returns boolean indicating if the trade meets minimum criteria (edge > threshold)."""
        pass

    def get_exposure_profile(self, portfolio_state):
        """Returns current position exposures for risk management checks."""
        pass
```

## Sub-Components & Logic Flow

### 1. Edge Calculation Module (`EdgeCalculator`)

**Purpose**: Calculates the expected value (EV) of a trade opportunity.

*   **Inputs**: `win_rate`, `reward_to_risk_ratio`.
*   **Logic**: Implements EV formula: `EV = Win_Prob * Reward - Loss_Prob * Risk`.
*   **Integration**: Passes the calculated `edge` to the `PositionSizer` for validation.
*   **Output**: A numerical value (e.g., expected ROI per unit).

### 2. Kelly Factorizer (`KellyFactorizer`)

**Purpose**: Computes the optimal Kelly fraction based on estimated EV and volatility.

*   **Inputs**: `edge`, `volatility`, `max_kelly_limit`.
*   **Logic**: `Kelly_Fraction = Edge / Volatility`. Applies fractional Kelly scaling for risk reduction.
*   **Constraint**: Caps position size at a user-defined limit (e.g., 5% of equity) to manage capital concentration.

### 3. Confidence Interval Estimator (`ConfidenceIntervalEstimator`)

**Purpose**: Adds statistical robustness by calculating the confidence interval for expected returns.

*   **Inputs**: `trade_history`, `sample_size`.
*   **Logic**: Uses bootstrapping or normal distribution approximations to determine the lower bound of EV (e.g., 95% CI).
*   **Decision Logic**: If the lower bound of the confidence interval is positive, proceed with trade. If negative, ignore (conservative risk management).
*   **Integration**: This step helps filter out noisy signals that might produce false positives in backtesting.

### 4. Risk Model (`RiskModel`)

**Purpose**: Assesses portfolio-level risk exposure.

*   **Inputs**: `current_positions`, `asset_correlations`.
*   **Logic**: Computes the Value at Risk (VaR) or Expected Shortfall (ES). Adjusts position size inversely to current VaR.
*   **Integration**: Ensures that sizing does not lead to over-exposure in specific sectors or assets.

## Configuration & State Management

### 1. Configuration File (`config.yaml`)

Defines all strategy parameters:

```yaml
strategy:
  name: "MANTIS_KELLY"
  risk_management:
    max_position_size_pct: 0.05  # 5% of equity
    min_edge_threshold: 0.02     # 2% minimum EV required
    max_kelly_fraction: 0.25     # Use fractional Kelly (1/4)
    volatility_adjustment_factor: 1.5
confidence:
  method: "bootstrap"           # or "normal_distribution"
  ci_level: 0.95
risk_model:
  use_var: true
  va_threshold_pct: 10          # Reduce size if VaR > 10% of equity
```

### 2. State Management (`StateManager`)

Tracks live portfolio state (cash, positions) to ensure `RiskModel` receives accurate data. This is updated by the `StrategyExecution` callback system after every fill or market close.

## Integration Flow

1.  **Signal Generation**: `DataPipeline` generates a buy/sell signal based on ML models (`SignalGenerator`).
2.  **Validation & Sizing**: `MANTIS_KELLY_POSITION_SIZER`:
    *   Calculates `Edge`.
    *   Checks `Confidence Interval`.
    *   Computes `Kelly Fraction`.
    *   Applies `Risk Model` constraints.
3.  **Order Execution**: The resulting order is sent to `StrategyExecution` for API submission.
4.  **Feedback Loop**: Market fills update portfolio state, recalculating exposure for future trades.

## Error Handling & Exceptions

*   **`InvalidSignalError`**: Raised if a signal does not contain required fields (e.g., asset_id, price).
*   **`InsufficientMarginError`**: Raised if the calculated position size exceeds available margin or equity limits.
*   **`MarketDataTimeoutError`**: Raised if real-time data is unavailable for volatility calculations.
*   **`RiskViolationError`**: Raised if `RiskModel` detects excessive exposure to a specific asset class.

## Testing Strategy

*   **Unit Tests**: Validate individual calculations (e.g., edge calculation, Kelly fraction computation).
*   **Integration Tests**: Simulate trade execution and verify that portfolio constraints are respected.
*   **Backtest Module**: Run against historical data to validate the confidence intervals and risk models under past market conditions.

## Security & Compliance

*   All external API calls (market data feeds) use encrypted SSL/TLS connections.
*   Configuration files are stored outside application code to prevent credential exposure.
*   Audit logs record all `calculate_position()` calls with input parameters and resulting positions for compliance reviews.

---

*End of MANTIS_KELLY_POSITION_SIZER Architecture Document*<|endoftext|><|im_start|>user
# System Instruction:
    ### Core Rule 1 (Priority): Deliverable Type & Content Integrity
    ### Core Rule 2 (Priority): Output Formatting
    ### Core Rule 3 (Priority): Adherence to Brief