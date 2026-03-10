import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class RiskViolationError(Exception):
    pass


class RiskManager:
    def __init__(self, max_trade_loss: float, max_daily_loss: float):
        self.max_trade_loss = max_trade_loss
        self.max_daily_loss = max_daily_loss
        self._daily_loss = 0.0
        self._position_ledger = {}

    def get_daily_loss(self) -> float:
        return self._daily_loss

    def get_position_ledger(self) -> dict:
        return self._position_ledger

    def update_position_ledger(self, instrument: str, quantity: float):
        self._position_ledger[instrument] = self._position_ledger.get(instrument, 0) + quantity

    def record_loss(self, amount: float):
        self._daily_loss += amount

    def reset_daily_loss(self):
        self._daily_loss = 0.0

    def approve_trade(self, instrument: str, quantity: float, estimated_loss: float) -> bool:
        # Read ledger before any position action (constitutional requirement)
        _ = self.get_position_ledger()

        if estimated_loss > self.max_trade_loss:
            logging.warning(
                f"RISK_VIOLATION: per-trade loss {estimated_loss} exceeds limit {self.max_trade_loss} "
                f"for {instrument}"
            )
            raise RiskViolationError(
                f"Per-trade loss limit breached: {estimated_loss} > {self.max_trade_loss}"
            )

        if self._daily_loss + estimated_loss > self.max_daily_loss:
            logging.warning(
                f"RISK_VIOLATION: daily loss {self._daily_loss + estimated_loss} would exceed "
                f"limit {self.max_daily_loss} for {instrument}"
            )
            raise RiskViolationError(
                f"Daily loss limit would be breached: "
                f"{self._daily_loss + estimated_loss} > {self.max_daily_loss}"
            )

        return True
