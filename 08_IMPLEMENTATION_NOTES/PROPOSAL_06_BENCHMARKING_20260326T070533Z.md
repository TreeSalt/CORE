---
DOMAIN: 06_BENCHMARKING
MODEL: qwen3.5:4b
TIER: sprinter
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

import abc
from abc import ABC, abstractmethod
import pytest


class Strategy(ABC):
    """Base class for trading strategies."""
    
    @abstractmethod
    def position_size(self) -> float:
        pass
    
    @abstractmethod
    def should_exit_stop_loss(self, current_price: float, stop_loss_price: float) -> bool:
        pass


class ConcreteStrategy(Strategy):
    """A concrete strategy implementation."""
    
    def __init__(self, pos: float = 1.0, price: float = 50.0, sl: float = 40.0):
        self._position_size = pos
        self.current_price = price
        self.stop_loss_price = sl

    def position_size(self) -> float:
        return self._position_size

    def should_exit_stop_loss(self, current_price: float, stop_loss_price: float) -> bool:
        # Returns True if the current price is at the stop loss level
        return abs(current_price - stop_loss_price) < 1e-6


# Test suite
def test_cannot_instantiate_abstract(strategy: Strategy):
    """Ensure Strategy cannot be instantiated directly."""
    with pytest.raises(TypeError):
        Strategy()


def test_concrete_strategy_works(concrete: ConcreteStrategy):
    """Ensure concrete strategy can be instantiated and has position size."""
    assert isinstance(concrete, ConcreteStrategy)
    assert concrete.position_size() == 1.0


def test_position_size_returns_float(strategy: Strategy, concrete: ConcreteStrategy):
    """Verify position_size returns a float."""
    result = concrete.position_size()
    assert isinstance(result, float)
    assert type(result).__name__ == "float"


def test_should_exit_stop_loss(concrete: ConcreteStrategy):
    """Verify exit triggers when price hits stop loss."""
    # Test case 1: At stop loss
    assert concrete.should_exit_stop_loss(40.0, 40.0) is True
    
    # Test case 2: Above stop loss (no exit)
    assert concrete.should_exit_stop_loss(50.0, 40.0) is False


# Helper classes for testing isolation (mocking the imports if necessary for standalone execution)
class StrategyTestHelper:
    """Helper to support the test file."""
    pass