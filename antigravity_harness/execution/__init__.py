"""
antigravity_harness.execution — Institutional Execution Layer
==============================================================
Provides the MASTER_SKILL v1.2.2 execution stack:
- ExecutionAdapter (ABCs)
- ExecutionSafety (Survival Mode)
- FillTape (Deterministic Recording)
- FlattenManager (Widowmaker Guard)
- SimExecutionAdapter (Deterministic Simulation)
- RolloverGuard (Contract Management)
"""
from antigravity_harness.execution.adapter_base import (
    ExecutionAdapter,
    CalendarAdapter,
    OrderIntent,
    OrderAck,
    Fill,
    Position,
    OrderSide,
    OrderType,
    OrderStatus,
)
from antigravity_harness.execution.fill_tape import FillTape
from antigravity_harness.execution.flatten_manager import FlattenManager
from antigravity_harness.execution.safety import ExecutionSafety
from antigravity_harness.execution.sim_adapter import SimExecutionAdapter
from antigravity_harness.execution.rollover import RolloverGuard, RolloverError

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
