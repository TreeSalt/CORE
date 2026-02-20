from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    pass

import pandas as pd
from pydantic import BaseModel, ConfigDict, Field

from antigravity_harness.accelerators.vector_cache import VectorCache
from antigravity_harness.config import (
    DataConfig,
    EngineConfig,
    GateThresholds,
    StrategyParams,
)
from antigravity_harness.types import Money, Price, Quantity


class Trade(BaseModel):
    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)
    entry_time: pd.Timestamp
    exit_time: pd.Timestamp
    entry_price: Price
    exit_price: Price
    qty: Quantity
    pnl_abs: Money
    pnl_pct: float
    exit_reason: str

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()

class MetricSet(BaseModel):
    """
    Standardized Performance Metrics.
    Eliminates "magic string" lookups and ensures float integrity.
    """

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    trade_count: int = Field(default=0)
    profit_factor: float = Field(default=0.0)
    sharpe_ratio: float = Field(default=0.0)
    max_dd_pct: float = Field(default=0.0)
    expectancy_pct: float = Field(default=0.0, alias="expectancy")
    win_rate: float = Field(default=0.0)
    cagr: float = Field(default=0.0)
    calmar_ratio: float = Field(default=0.0, alias="calmar")
    gross_profit: float = Field(default=0.0)
    gross_loss: float = Field(default=0.0)
    profit_score: float = Field(default=0.0)
    annualized_vol: float = Field(default=0.0)
    raw_entry_signals: int = Field(default=0)
    raw_exit_signals: int = Field(default=0)

    # Heavy Data
    equity_curve: Dict[str, float] = Field(default_factory=dict)
    trades: List[Dict[str, Any]] = Field(default_factory=list)


class BacktestResult(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, frozen=True)
    equity_curve: pd.Series
    trades: List[Trade]
    metrics: MetricSet
    config: Dict[str, Any]
    trace: pd.DataFrame = Field(default_factory=pd.DataFrame)


class GateResult(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, frozen=True)
    gate: str
    status: str  # PASS, WARN, FAIL
    reason: str
    metrics: Dict[str, Any] = Field(default_factory=dict)
    trace: Optional[pd.DataFrame] = None

    @property
    def passed(self) -> bool:
        return self.status in ["PASS", "WARN"]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "gate": self.gate,
            "status": self.status,
            "reason": self.reason,
            "metrics": self.metrics,
        }

    @property
    def details(self) -> Dict[str, Any]:
        return self.metrics




class SimulationResult(BaseModel):
    """
    The canonical output of a SovereignRunner simulation.
    Strictly types the result to avoid dict-based ambiguity.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True, frozen=True)

    params: Dict[str, Any]
    status: str
    profit_status: str
    safety_status: str
    fail_reason: str
    warns: List[str]
    gate_results: List[GateResult]
    metrics: MetricSet
    trace: Optional[pd.DataFrame] = Field(default=None, exclude=True)


class SimulationContext(BaseModel):
    """
    The "Crystal Palace" Pillar 2: Context Injection.
    Encapsulates all inputs required for a simulation run.
    Ensures physics alignment (is_crypto, periods) before execution.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True, frozen=True)

    strategy_name: str
    strategy: Any  # Strategy instance
    params: StrategyParams
    data_cfg: DataConfig
    engine_cfg: EngineConfig
    thresholds: GateThresholds
    symbol: str
    start: str
    end: str
    gate_profile: str = "equity_fortress"
    override_df: Optional[pd.DataFrame] = None
    intelligence: Dict[str, Any] = Field(default_factory=dict)
    debug: bool = False
    out_dir: Optional[Path] = None
    vector_cache: Optional[VectorCache] = None
