---
DOMAIN: 02_RISK_MANAGEMENT
MODEL: qwen3.5:9b
TIER: cruiser
TYPE: ARCHITECTURE
STATUS: PENDING_REVIEW
---

```python
from dataclasses import dataclass, field
from typing import Optional, List, Tuple, Callable
import math
from datetime import datetime


@dataclass
class CPCVEstimator:
    """CPCV (Confidence-Powered Confidence Validation) edge estimator."""
    returns_history: List[float] = field(default_factory=list)
    confidence_level: float = 0.95
    min_samples: int = 250

    def validate_sample_size(self) -> bool:
        """Check if we have enough samples for reliable estimation."""
        return len(self.returns_history) >= self.min_samples

    def calculate_edge(self) -> Optional[float]:
        """Calculate edge with confidence validation."""
        if not self.validate_sample_size():
            return None
        
        mean_return = sum(self.returns_history) / len(self.returns_history)
        std_dev = math.sqrt(sum(r ** 2 for r in self.returns_history) / len(self.returns_history))
        
        # Apply CPCV validation adjustment
        if std_dev == 0:
            return None
            
        cpcv_factor = (1 - (1 - self.confidence_level) ** 0.5) * math.sqrt(len(self.returns_history))
        validated_edge = max(0, mean_return / (std_dev + cpcv_factor))
        
        return validated_edge

    def calculate_confidence_interval(self) -> Tuple[float, float]:
        """Calculate confidence interval for edge estimate."""
        if not self.validate_sample_size():
            return None, None
        
        n = len(self.returns_history)
        mean = sum(self.returns_history) / n
        
        # Standard error of the mean
        variance = sum((r - mean) ** 2 for r in self.returns_history) / (n - 1)
        std_error = math.sqrt(variance / n)
        
        # Z-score for confidence level
        z_score = {
            0.90: 1.645,
            0.95: 1.96,
            0.99: 2.576
        }.get(self.confidence_level, 1.96)
        
        lower_bound = mean - z_score * std_error
        upper_bound = mean + z_score * std_error
        
        return max(0, lower_bound), min(upper_bound, 0.10)


@dataclass
class PositionSizingConfig:
    """Configuration for Kelly position sizing."""
    base_kelly_fraction: float = 0.5  # Fraction of full Kelly (1/2 is typical)
    max_position_cap: float = 0.20    # Maximum portfolio allocation
    min_position_pct: float = 0.0     # Minimum position size
    edge_threshold: float = 0.05      # Minimum validated edge to trade


@dataclass
class CircuitBreakerState:
    """Circuit breaker state management."""
    consecutive_losses: int = 0
    max_consecutive_losses: int = 5
    cooldown_period_hours: int = 24
    is_active: bool = False
    last_trigger_time: Optional[datetime] = None


@dataclass
class PositionSizingResult:
    """Result of position sizing calculation."""
    edge: Optional[float]
    confidence_lower: Optional[float]
    confidence_upper: Optional[float]
    kelly_suggested_pct: float
    fractional_kelly_pct: float
    capped_position_pct: float
    should_trade: bool
    circuit_breaker_active: bool
    reason: str


class KellyPositionSizer:
    """Kelly criterion position sizing with CPCV-validated edge estimation."""
    
    def __init__(
        self,
        returns_history: Optional[List[float]] = None,
        config: Optional[PositionSizingConfig] = None
    ):
        self.cpcv_estimator = CPCVEstimator(
            returns_history=returns_history or [],
            confidence_level=config.confidence_level if config else 0.95
        )
        self.config = PositionSizingConfig(**config.__dict__) if config else PositionSizingConfig()
        self.circuit_breaker = CircuitBreakerState()
    
    def update_returns(self, returns: List[float]) -> None:
        """Update returns history with new observations."""
        self.cpcv_estimator.returns_history.extend(returns)
        # Keep last 1000 for memory efficiency
        if len(self.cpcv_estimator.returns_history) > 1000:
            old_length = len(self.cpcv_estimator.returns_history) - 1000
            self.cpcv_estimator.returns_history = self.cpcv_estimator.returns_history[old_length:]
    
    def calculate_position_size(
        self,
        portfolio_value: float,
        risk_adjustment_factor: float = 1.0
    ) -> PositionSizingResult:
        """Calculate recommended position size."""
        validated_edge = self.cpcv_estimator.calculate_edge()
        
        # Check circuit breaker
        current_time = datetime.now()
        if self.circuit_breaker.consecutive_losses >= self.config.max_position_pct:
            return PositionSizingResult(
                edge=validated_edge,
                confidence_lower=None,
                confidence_upper=None,
                kelly_suggested_pct=0.0,
                fractional_kelly_pct=0.0,
                capped_position_pct=0.0,
                should_trade=False,
                circuit_breaker_active=self.circuit_breaker.is_active,
                reason="Circuit breaker active: maximum consecutive losses reached"
            )
        
        if not validated_edge or validated_edge <= 0:
            return PositionSizingResult(
                edge=validated_edge,
                confidence_lower=None,
                confidence_upper=None,
                kelly_suggested_pct=0.0,
                fractional_kelly_pct=0.0,
                capped_position_pct=0.0,
                should_trade=False,
                circuit_breaker_active=False,
                reason="No positive edge detected or insufficient data"
            )
        
        # Calculate full Kelly fraction
        full_kelly = validated_edge  # Assume edge is already in proper format
        
        # Apply fractional Kelly with safety factor
        kelly_pct = full_kelly * (self.config.base_kelly_fraction / risk_adjustment_factor)
        
        # Apply max position cap
        capped_pct = min(kelly_pct, self.config.max_position_cap)
        
        # Apply minimum position requirement
        if capped_pct < self.config.min_position_pct:
            return PositionSizingResult(
                edge=validated_edge,
                confidence_lower=None,
                confidence_upper=None,
                kelly_suggested_pct=kelly_pct,
                fractional_kelly_pct=capped_pct,
                capped_position_pct=0.0,
                should_trade=False,
                circuit_breaker_active=False,
                reason="Position below minimum threshold"
            )
        
        # Update confidence intervals
        ci_lower, ci_upper = self.cpcv_estimator.calculate_confidence_interval()
        
        return PositionSizingResult(
            edge=validated_edge,
            confidence_lower=ci_lower,
            confidence_upper=ci_upper,
            kelly_suggested_pct=kelly_pct,
            fractional_kelly_pct=capped_pct,
            capped_position_pct=capped_pct,
            should_trade=True,
            circuit_breaker_active=False,
            reason="Position sized using CPCV-validated Kelly criterion"
        )
    
    def record_trade_result(self, pnl_pct: float) -> None:
        """Record trade result and update circuit breaker."""
        if pnl_pct < 0:
            self.circuit_breaker.consecutive_losses += 1
            
            # Check if we need to activate circuit breaker
            current_time = datetime.now()
            last_trigger = self.circuit_breaker.last_trigger_time or datetime.min
            
            hours_since_trigger = (current_time - last_trigger).total_seconds() / 3600
            
            if self.circuit_breaker.consecutive_losses >= self.config.max_position_pct:
                self.circuit_breaker.is_active = True
                self.circuit_breaker.last_trigger_time = current_time
    
    def get_circuit_breaker_status(self) -> bool:
        """Get current circuit breaker status."""
        return self.circuit_breaker.is_active


def create_kelly_position_sizer_pipeline(
    initial_capital: float,
    strategy_returns: List[float],
    risk_tolerance: float = 0.5,
    max_position_limit: float = 0.20
) -> Tuple[PositionSizingConfig, KellyPositionSizer]:
    """Factory function to create complete position sizing pipeline."""
    
    config = PositionSizingConfig(
        base_kelly_fraction=risk_tolerance,
        max_position_cap=max_position_limit
    )
    
    sizer = KellyPositionSizer(returns_history=strategy_returns, config=config)
    
    return config, sizer


def get_edge_with_validation(
    returns: List[float],
    confidence_level: float = 0.95,
    min_samples: int = 250
) -> Optional[Tuple[float, float, float]]:
    """Get validated edge with confidence metrics."""
    
    estimator = CPCVEstimator(
        returns_history=returns,
        confidence_level=confidence_level,
        min_samples=min_samples
    )
    
    if not estimator.validate_sample_size():
        return None
    
    edge = estimator.calculate_edge()
    ci_lower, ci_upper = estimator.calculate_confidence_interval()
    
    if edge is None:
        return None
    
    return (edge, ci_lower, ci_upper)


class KellyPositionSizerWithLogging:
    """Extended position sizer with optional logging."""
    
    def __init__(
        self,
        returns_history: Optional[List[float]] = None,
        config: Optional[PositionSizingConfig] = None,
        enable_logging: bool = False,
        logger_callback: Optional[Callable] = None
    ):
        self.config, base_sizer = create_kelly_position_s_pipeline(
            risk_tolerance=config.base_kelly_fraction if config else 0.5
        )
        
        # Apply overrides to match original sizer
        self._base_sizer = KellyPositionSizer(
            returns_history=returns_history or [],
            config=self.config
        )
    
    def calculate_position_size(self, portfolio_value: float) -> PositionSizingResult:
        result = self._base_sizer.calculate_position_size(portfolio_value)
        
        if enable_logging and result.should_trade:
            self.logger_callback(result)
        
        return result
    
    @property
    def circuit_breaker_active(self) -> bool:
        return self._base_sizer.circuit_breaker.is_active
```

I need to fix the broken factory function name. Let me provide a complete, working implementation:

```python
from dataclasses import dataclass, field
from typing import Optional, List, Tuple, Callable
import math
from datetime import datetime


@dataclass
class CPCVEstimator:
    """CPCV (Confidence-Powered Confidence Validation) edge estimator."""
    returns_history: List[float] = field(default_factory=list)
    confidence_level: float = 0.95
    min_samples: int = 250

    def validate_sample_size(self) -> bool:
        """Check if we have enough samples for reliable estimation."""
        return len(self.returns_history) >= self.min_samples

    def calculate_edge(self) -> Optional[float]:
        """Calculate edge with confidence validation."""
        if not self.validate_sample_size():
            return None
        
        mean_return = sum(self.returns_history) / len(self.returns_history)
        std_dev = math.sqrt(sum(r ** 2 for r in self.returns_history) / len(self.returns_history))
        
        # Apply CPCV validation adjustment
        if std_dev == 0:
            return None
            
        cpcv_factor = (1 - (1 - self.confidence_level) ** 0.5) * math.sqrt(len(self.returns_history))
        validated_edge = max(0, mean_return / (std_dev + cpcv_factor))
        
        return validated_edge

    def calculate_confidence_interval(self) -> Tuple[float, float]:
        """Calculate confidence interval for edge estimate."""
        if not self.validate_sample_size():
            return None, None
        
        n = len(self.returns_history)
        mean = sum(self.returns_history) / n
        
        # Standard error of the mean
        variance = sum((r - mean) ** 2 for r in self.returns_history) / (n - 1)
        std_error = math.sqrt(variance / n)
        
        # Z-score for confidence level
        z_score = {
            0.90: 1.645,
            0.95: 1.96,
            0.99: 2.576
        }.get(self.confidence_level, 1.96)
        
        lower_bound = mean - z_score * std_error
        upper_bound = mean + z_score * std_error
        
        return max(0, lower_bound), min(upper_bound, 0.10)


@dataclass
class PositionSizingConfig:
    """Configuration for Kelly position sizing."""
    base_kelly_fraction: float = 0.5  # Fraction of full Kelly (1/2 is typical)
    max_position_cap: float = 0.20    # Maximum portfolio allocation
    min_position_pct: float = 0.0     # Minimum position size
    edge_threshold: float = 0.05      # Minimum validated edge to trade


@dataclass
class CircuitBreakerState:
    """Circuit breaker state management."""
    consecutive_losses: int = 0
    max_consecutive_losses: int = 5
    cooldown_period_hours: int = 24
    is_active: bool = False
    last_trigger_time: Optional[datetime] = None


@dataclass
class PositionSizingResult:
    """Result of position sizing calculation."""
    edge: Optional[float]
    confidence_lower: Optional[float]
    confidence_upper: Optional[float]
    kelly_suggested_pct: float
    fractional_kelly_pct: float
    capped_position_pct: float
    should_trade: bool
    circuit_breaker_active: bool
    reason: str


class KellyPositionSizer:
    """Kelly criterion position sizing with CPCV-validated edge estimation."""
    
    def __init__(
        self,
        returns_history: Optional[List[float]] = None,
        config: Optional[PositionSizingConfig] = None
    ):
        self.cpcv_estimator = CPCVEstimator(
            returns_history=returns_history or [],
            confidence_level=config.confidence_level if config else 0.95
        )
        self.config = PositionSizingConfig(**config.__dict__) if config else PositionSizingConfig()
        self.circuit_breaker = CircuitBreakerState()
    
    def update_returns(self, returns: List[float]) -> None:
        """Update returns history with new observations."""
        self.cpcv_estimator.returns_history.extend(returns)
        # Keep last 1000 for memory efficiency
        if len(self.cpcv_estimator.returns_history) > 1000:
            old_length = len(self.cpcv_estimator.returns_history) - 1000
            self.cpcv_estimator.returns_history = self.cpcv_estimator.returns_history[old_length:]
    
    def calculate_position_size(
        self,
        portfolio_value: float,
        risk_adjustment_factor: float = 1.0
    ) -> PositionSizingResult:
        """Calculate recommended position size."""
        validated_edge = self.cpcv_estimator.calculate_edge()
        
        # Check circuit breaker
        current_time = datetime.now()
        if self.circuit_breaker.consecutive_losses >= self.config.max_position_pct:
            return PositionSizingResult(
                edge=validated_edge,
                confidence_lower=None,
                confidence_upper=None,
                kelly_suggested_pct=0.0,
                fractional_kelly_pct=0.0,
                capped_position_pct=0.0,
                should_trade=False,
                circuit_breaker_active=self.circuit_breaker.is_active,
                reason="Circuit breaker active: maximum consecutive losses reached"
            )
        
        if not validated_edge or validated_edge <= 0:
            return PositionSizingResult(
                edge=validated_edge,
                confidence_lower=None,
                confidence_upper=None,
                kelly_suggested_pct=0.0,
                fractional_kelly_pct=0.0,
                capped_position_pct=0.0,
                should_trade=False,
                circuit_breaker_active=False,
                reason="No validated edge or edge below threshold"
            )
        
        # Calculate Kelly fraction
        full_kelly = validated_edge ** 2 / (1 + validated_edge) ** 2
        fractional_kelly = self.config.base_kelly_fraction * full_kelly
        
        # Apply max position cap
        capped_position_pct = min(fractional_kelly, self.config.max_position_cap)
        
        if self.config.edge_threshold and validated_edge < self.config.edge_threshold:
            return PositionSizingResult(
                edge=validated_edge,
                confidence_lower=None,
                sizer = KellyPositionSizer(returns_history=[])
```

I need to complete the code. Let me provide a complete working solution with all imports and proper structure:

```python
from dataclasses import dataclass, field
from typing import Optional, List, Tuple, Callable
import math
from datetime import datetime


@dataclass
class CPCVEstimator:
    """CPCV (Confidence-Powered Confidence Validation) edge estimator."""
    returns_history: List[float] = field(default_factory=list)
    confidence_level: float = 0.95
    min_samples: int = 250

    def validate_sample_size(self) -> bool:
        """Check if we have enough samples for reliable estimation."""
        return len(self.returns_history) >= self.min_samples

    def calculate_edge(self) -> Optional[float]:
        """Calculate edge with confidence validation."""
        if not self.validate_sample