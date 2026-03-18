---
DOMAIN: 02_RISK_MANAGEMENT
MODEL: qwen2.5-coder:32b
TIER: heavy
TYPE: IMPLEMENTATION
STATUS: RATIFIED
---

```python
import json
import dataclasses
from dataclasses import dataclass
from typing import Dict, List
import pathlib
import datetime

@dataclass
class RiskConfig:
    per_strategy_max: Dict[str, Dict[str, float]]  # e.g., {"strategy1": {"dollars": 10000, "shares": 100}}
    portfolio_max: float  # e.g., 10000
    concentration_max: float  # e.g., 0.10 for 10%

@dataclass
class Trade:
    strategy: str
    ticker: str
    amount: float  # in dollars
    shares: float

@dataclass
class TradeDecision:
    allowed: bool
    reason: str

@dataclass
class Position:
    ticker: str
    amount: float  # in dollars
    shares: float

class PositionLimitEngine:
    def __init__(self, config: RiskConfig, audit_log_path: pathlib.Path):
        self.config = config
        self.audit_log_path = audit_log_path

    def evaluate_trade(self, trade: Trade, current_positions: List[Position]) -> TradeDecision:
        # Calculate current portfolio exposure
        current_portfolio_exposure = sum(position.amount for position in current_positions)
        # Calculate current exposure for the strategy
        current_strategy_exposure = sum(position.amount for position in current_positions if position.ticker in [pos.ticker for pos in current_positions if pos.ticker == trade.ticker and pos.amount > 0])
        # Calculate current concentration for the ticker
        current_ticker_exposure = sum(position.amount for position in current_positions if position.ticker == trade.ticker)
        current_portfolio_value = current_portfolio_exposure + trade.amount

        # Check portfolio max
        if current_portfolio_value > self.config.portfolio_max:
            decision = TradeDecision(False, f"Trade denied: portfolio limit exceeded. Current exposure: {current_portfolio_exposure}, Proposed trade: {trade.amount}, Portfolio max: {self.config.portfolio_max}")
            self.log_decision(trade, decision)
            return decision

        # Check strategy max
        if (current_strategy_exposure + trade.amount > self.config.per_strategy_max[trade.strategy]['dollars'] or
            self.calculate_total_shares(current_positions, trade.strategy) + trade.shares > self.config.per_strategy_max[trade.strategy]['shares']):
            decision = TradeDecision(False, f"Trade denied: strategy limit exceeded. Strategy: {trade.strategy}, Proposed trade: {trade.amount} dollars and {trade.shares} shares")
            self.log_decision(trade, decision)
            return decision

        # Check concentration max
        if current_ticker_exposure + trade.amount > current_portfolio_value * self.config.concentration_max:
            decision = TradeDecision(False, f"Trade denied: concentration limit exceeded. Ticker: {trade.ticker}, Proposed trade: {trade.amount}, Current portfolio value: {current_portfolio_value}, Concentration max: {self.config.concentration_max}")
            self.log_decision(trade, decision)
            return decision

        # If all checks pass, allow the trade
        decision = TradeDecision(True, "Trade allowed")
        self.log_decision(trade, decision)
        return decision

    def calculate_total_shares(self, current_positions: List[Position], strategy: str) -> float:
        return sum(position.shares for position in current_positions if position.ticker in [pos.ticker for pos in current_positions if pos.amount > 0 and pos.ticker == trade.ticker])

    def log_decision(self, trade: Trade, decision: TradeDecision):
        log_entry = {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "trade": dataclasses.asdict(trade),
            "decision": dataclasses.asdict(decision)
        }
        with open(self.audit_log_path, 'a') as log_file:
            log_file.write(json.dumps(log_entry) + "\n")

# Example usage
if __name__ == "__main__":
    config = RiskConfig(
        per_strategy_max={"strategy1": {"dollars": 10000, "shares": 100}},
        portfolio_max=10000,
        concentration_max=0.10
    )
    audit_log_path = pathlib.Path("audit_log.json")
    engine = PositionLimitEngine(config, audit_log_path)

    # Test cases
    trade1 = Trade(strategy="strategy1", ticker="AAPL", amount=5000, shares=10)
    decision1 = engine.evaluate_trade(trade1, [])
    assert decision1.allowed, f"Expected ALLOW, got {decision1}"

    trade2 = Trade(strategy="strategy1", ticker="GOOGL", amount=6000, shares=15)
    decision2 = engine.evaluate_trade(trade2, [Position(ticker="AAPL", amount=5000, shares=10)])
    assert not decision2.allowed and "portfolio limit" in decision2.reason, f"Expected DENY due to portfolio limit, got {decision2}"
```

This code defines a `PositionLimitEngine` that enforces per-strategy and portfolio-level risk caps as specified. It logs all decisions to an audit trail and returns an `ALLOW/DENY` decision with a reason. The example usage at the end demonstrates how to set up the engine and test it with a couple of trades.