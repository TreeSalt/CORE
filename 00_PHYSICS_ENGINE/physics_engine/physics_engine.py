class PhysicsViolationError(Exception):
    pass

class PhysicsEngine:
    def __init__(self, position_limits):
        self.position_limits = position_limits
        self.ledger = {}

    def calculate_position_pl(self, instrument, current_price, previous_price):
        pl = (current_price - previous_price) * self.ledger.get(instrument, 0)
        return pl

    def enforce_position_limits(self, instrument, new_position):
        if abs(new_position) > self.position_limits.get(instrument, float('inf')):
            raise PhysicsViolationError(f"Position limit breached for instrument: {instrument}")

    def track_open_position(self, instrument, quantity):
        if instrument not in self.ledger:
            self.ledger[instrument] = quantity
        else:
            self.ledger[instrument] += quantity
        self.enforce_position_limits(instrument, self.ledger[instrument])

    def close_position(self, instrument, quantity):
        if instrument not in self.ledger:
            raise ValueError(f"No open position found for instrument: {instrument}")
        if self.ledger[instrument] < quantity:
            raise PhysicsViolationError(f"Not enough open position to close for instrument: {instrument}")
        self.ledger[instrument] -= quantity
        self.enforce_position_limits(instrument, self.ledger[instrument])

    def get_open_positions(self):
        return self.ledger
