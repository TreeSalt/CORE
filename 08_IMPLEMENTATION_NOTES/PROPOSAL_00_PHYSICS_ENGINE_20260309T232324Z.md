---
DOMAIN: 00_PHYSICS_ENGINE
STATUS: RATIFIED
---

**Proposal for PhysicsEngine Class Implementation**

### Overview
The PhysicsEngine class is designed to handle the calculation of position P&L using tick-accurate pricing, enforce position limits, track open positions in a ledger, and raise a PhysicsViolationError upon constraint breach. The class will be implemented in a way that adheres to the specified constraints.

### Class Structure
The PhysicsEngine class will consist of the following components:
1. **Initialization**: Sets up the necessary parameters and initializes the ledger.
2. **Position Calculation**: Calculates P&L based on tick-accurate pricing.
3. **Position Limit Enforcement**: Ensures that open positions do not exceed predefined limits.
4. **Open Position Tracking**: Maintains a ledger of open positions.
5. **Error Handling**: Raises a PhysicsViolationError upon constraint breach.

### Detailed Implementation
Below is a proposal for the PhysicsEngine class:

```python
class PhysicsEngine:
    def __init__(self, position_limits):
        """
        Initialize the PhysicsEngine with position limits.

        :param position_limits: A dictionary of position limits for each instrument.
        """
        self.position_limits = position_limits
        self.ledger = {}

    def calculate_position_pl(self, instrument, current_price, previous_price):
        """
        Calculate the P&L for a given instrument using tick-accurate pricing.

        :param instrument: The instrument to calculate P&L for.
        :param current_price: The current price of the instrument.
        :param previous_price: The previous price of the instrument.
        :return: The P&L amount.
        """
        # Calculate P&L based on current and previous prices
        pl = (current_price - previous_price) * self.ledger.get(instrument, 0)
        return pl

    def enforce_position_limits(self, instrument, new_position):
        """
        Enforce position limits for a given instrument.

        :param instrument: The instrument to enforce limits for.
        :param new_position: The new position to be checked.
        :raises PhysicsViolationError: If the new position breaches the limit.
        """
        if abs(new_position) > self.position_limits.get(instrument, float('inf')):
            raise PhysicsViolationError(f"Position limit breached for instrument: {instrument}")

    def track_open_position(self, instrument, quantity):
        """
        Track the open position for a given instrument.

        :param instrument: The instrument to track.
        :param quantity: The quantity of the position to track.
        """
        if instrument not in self.ledger:
            self.ledger[instrument] = quantity
        else:
            self.ledger[instrument] += quantity

        # Enforce position limits after tracking the new position
        self.enforce_position_limits(instrument, self.ledger[instrument])

    def close_position(self, instrument, quantity):
        """
        Close a position for a given instrument.

        :param instrument: The instrument to close.
        :param quantity: The quantity of the position to close.
        :raises PhysicsViolationError: If closing the position would breach the limit.
        """
        if instrument not in self.ledger:
            raise ValueError(f"No open position found for instrument: {instrument}")

        if self.ledger[instrument] < quantity:
            raise PhysicsViolationError(f"Not enough open position to close for instrument: {instrument}")

        self.ledger[instrument] -= quantity
        self.enforce_position_limits(instrument, self.ledger[instrument])

    def get_open_positions(self):
        """
        Get the current open positions.

        :return: A dictionary of open positions.
        """
        return self.ledger
```

### Error Handling
The PhysicsEngine class raises a PhysicsViolationError upon constraint breach. This error is a custom exception that can be defined as follows:

```python
class PhysicsViolationError(Exception):
    """
    Custom exception raised when a physics constraint is violated.
    """
    pass
```

### Usage Example
Here is an example of how the PhysicsEngine class can be used:

```python
# Define position limits for instruments
position_limits = {
    "AAPL": 10000,
    "GOOGL": 5000
}

# Initialize the PhysicsEngine
physics_engine = PhysicsEngine(position_limits)

# Track open positions
physics_engine.track_open_position("AAPL", 1500)
physics_engine.track_open_position("GOOGL", 2500)

# Calculate P&L
current_price_aapl = 180
previous_price_aapl = 170
pl_aapl = physics_engine.calculate_position_pl("AAPL", current_price_aapl, previous_price_aapl)
print(f"P&L for AAPL: {pl_aapl}")

# Close a position
physics_engine.close_position("AAPL", 500)
```

### Conclusion
The proposed PhysicsEngine class provides a robust framework for calculating position P&L, enforcing position limits, and tracking open positions. It adheres to the specified constraints and raises a PhysicsViolationError upon constraint breach.