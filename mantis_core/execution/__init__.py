"""
mantis_core.execution — Institutional Execution Layer
==============================================================
Provides the MASTER_SKILL v1.2.2 execution stack:
- ExecutionAdapter (ABCs)
- ExecutionSafety (Survival Mode)
- FillTape (Deterministic Recording)
- FlattenManager (Widowmaker Guard)
- SimExecutionAdapter (Deterministic Simulation)
- RolloverGuard (Contract Management)
"""
from mantis_core.execution.adapter_base import (
    CalendarAdapter,
    ExecutionAdapter,
    Fill,
    OrderAck,
    OrderIntent,
    OrderSide,
    OrderStatus,
    OrderType,
    Position,
)
from mantis_core.execution.fill_tape import FillTape
from mantis_core.execution.flatten_manager import FlattenManager
from mantis_core.execution.rollover import RolloverError, RolloverGuard
from mantis_core.execution.safety import ExecutionSafety
from mantis_core.execution.sim_adapter import SimExecutionAdapter

__all__ = [
    "ExecutionAdapter",
    "CalendarAdapter",
    "ExecutionSafety",
    "FillTape",
    "FlattenManager",
    "SimExecutionAdapter",
    "RolloverGuard",
    "RolloverError",
    "OrderIntent",
    "OrderAck",
    "Fill",
    "Position",
    "OrderSide",
    "OrderType",
    "OrderStatus",
]
