---
DOMAIN: 00_PHYSICS_ENGINE
MODEL: qwen3.5:4b
TIER: sprinter
TYPE: ARCHITECTURE
STATUS: PENDING_REVIEW
---

# MANTIS V2 ARCHITECTURE DESIGN

## 1. Overview
- **Framework**: Alpaca (Paper Trading)
- **Pattern**: Non-Singleton Dependency Injection (DI) Pattern
- **Strategy**: E13 Strategy Engine
- **Core Components**: `data_provider`, `regime_detector`, `trend_signal` (E13), `position_sizer` (E13), `executor`

## 2. Pipeline Architecture
### Data Ingestion
- **Data Provider**: Loads historical and real-time OHLCV data via Alpaca API.
- **Integration**: CPCV integration for compliance checks.

### Signal Generation
- **Detector**: Monitors market conditions to switch between regime states (e.g., High Volatility, Low Vol).
- **Signal Engine**: E13 `trend_signal` generates buy/sell signals based on technical indicators.
- **Position Sizing**: E13 `position_sizer` calculates optimal position size based on risk parameters.

### Execution
- **Executor**: Handles order management and execution logic through Alpaca API.
- **Risk Management**: Implements path-based regulation to ensure limits are respected (e.g., max drawdown).

## 3. Validation & Testing
- **Backtesting Framework**: Utilizes historical data on Alpaca for validation.
- **Simulation**: Runs "paper trading" scenarios to verify signal accuracy and execution latency.

## 4. Path A Regulation
- **Scope**: Risk limits (max loss per trade, max daily drawdown) and position sizing logic.
- **Validation**: Ensures strict adherence to risk parameters in all market conditions.

## 5. Deployment Strategy
- **Target**: Phased rollout on BTC/USD Alpaca account.
- **Monitoring**: Continuous monitoring of execution performance and signal accuracy.
- **Feedback Loop**: Automatic feedback integration into the E13 engine for adaptive learning.