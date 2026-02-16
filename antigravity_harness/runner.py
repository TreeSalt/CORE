from __future__ import annotations

import logging
from typing import List

from antigravity_harness.gates import _status_from_gate_results, evaluate_gates
from antigravity_harness.models import GateResult, MetricSet, SimulationContext, SimulationResult
from antigravity_harness.strategies.registry import STRATEGY_REGISTRY, StrategyRegistry

logger = logging.getLogger(__name__)


class SovereignRunner:
    """
    The Single Simulation Engine.
    Consolidates Data Load -> Strategy Execution -> Gate Evaluation -> Metric Analysis.
    Base class for Calibration, Autonomy, and Certification paths.
    """

    def __init__(self, registry: StrategyRegistry = STRATEGY_REGISTRY):
        self.registry = registry

    def run_simulation(self, ctx: SimulationContext) -> SimulationResult:
        """Execute a single simulation and return the consolidated result.

        Self-healing: any exception is caught and returned as FAIL, never crashes.
        """
        try:
            # 1. Evaluate Gates
            gate_results = evaluate_gates(ctx)

            # 2. Extract Overall Status
            p_status, s_status, status, warns, fails = _status_from_gate_results(gate_results)

            # 3. Consolidate Metrics
            metrics = self._extract_metrics(gate_results)

            # 4. Final Output Construction
            trace_df = None
            if gate_results and hasattr(gate_results[0], "trace"):
                trace_df = gate_results[0].trace

            return SimulationResult(
                params=ctx.params.model_dump(),
                status=status,
                profit_status=p_status,
                safety_status=s_status,
                fail_reason="; ".join(fails),
                warns=warns,
                gate_results=gate_results,
                metrics=metrics,
                trace=trace_df,
            )
        except Exception as e:
            # Mid-flight recovery: log error, return structured FAIL
            from antigravity_harness.phoenix import FlightRecorder  # noqa: PLC0415

            recorder = FlightRecorder.instance()
            recorder.record_error("SovereignRunner.run_simulation", e, severity="CRITICAL")
            recorder.record_recovery("SovereignRunner.run_simulation", "FAIL_SAFE_RETURN",
                                     f"Returned FAIL result instead of crashing: {e}")
            logger.error("Simulation failed (contained): %s", e)

            return SimulationResult(
                params=ctx.params.model_dump() if ctx.params else {},
                status="FAIL",
                profit_status="FAIL",
                safety_status="FAIL",
                fail_reason=f"RUNTIME_ERROR: {type(e).__name__}: {e}",
                warns=[],
                gate_results=[],
                metrics=MetricSet(),
                trace=None,
            )

    def _extract_metrics(self, gate_results: List[GateResult]) -> MetricSet:
        """Extract flat metrics from GateResult objects."""
        if not gate_results:
            return MetricSet()

        # Prefer metrics from GATE3 (Performance) if available
        g3 = next((g for g in gate_results if g.gate.startswith("GATE_SHARPE") or g.gate.startswith("GATE3")), None)
        metrics_source = g3.details if (g3 and g3.details) else {}
        if not metrics_source:
            # Fallback to the first gate results (e.g. GATE_MIN_TRADES)
            metrics_source = gate_results[0].details if gate_results[0].details else {}

        # Extract canoncial metrics
        # Use simple mapping, let Result model handle defaults
        return MetricSet(
            trade_count=int(metrics_source.get("trade_count", 0)),
            profit_factor=float(metrics_source.get("profit_factor", 0.0)),
            sharpe_ratio=float(metrics_source.get("sharpe_ratio", 0.0)),
            max_dd_pct=float(metrics_source.get("max_dd_pct", 0.0)),
            expectancy=float(metrics_source.get("expectancy_pct", 0.0)),
            win_rate=float(metrics_source.get("win_rate", 0.0)),
            cagr=float(metrics_source.get("cagr", 0.0)),
            calmar=float(metrics_source.get("calmar_ratio", 0.0)),
            gross_profit=float(metrics_source.get("gross_profit", 0.0)),
            gross_loss=float(metrics_source.get("gross_loss", 0.0)),
            profit_score=float(metrics_source.get("profit_score", 0.0)),
            annualized_vol=float(metrics_source.get("annualized_vol", 0.0)),
            raw_entry_signals=int(metrics_source.get("raw_entry_signals", 0)),
            raw_exit_signals=int(metrics_source.get("raw_exit_signals", 0)),
            equity_curve=metrics_source.get("equity_curve", {}),
            trades=metrics_source.get("trades", []),
        )
