"""
test_execution_safety.py — Execution Safety & MES Stack Tests
=============================================================
Tests for:
  1. ExecutionSafety guardrails (max position, rate limit, duplicate, calendar)
  2. FlattenManager Widowmaker logic
  3. FillTape slippage drift tracking
  4. SimAdapter basic execution
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock

from antigravity_harness.execution.adapter_base import (
    ExecutionAdapter,
    ExecutionError,
    Fill,
    Order,
    OrderSide,
    OrderType,
)
from antigravity_harness.execution.fill_tape import FillTape
from antigravity_harness.execution.flatten_manager import FlattenManager
from antigravity_harness.execution.safety import ExecutionSafety, SafetyConfig
from antigravity_harness.execution.sim_adapter import SimAdapter


# ===========================================================
# Fixtures
# ===========================================================

@pytest.fixture
def sim():
    """Fresh SimAdapter with defaults."""
    return SimAdapter(initial_cash=100_000.0, slippage_bps=5.0)


@pytest.fixture
def tape():
    """Fresh FillTape."""
    return FillTape(drift_alert_threshold_bps=50.0, rolling_window=5)


def _make_order(symbol="MES", side=OrderSide.BUY, qty=1.0, price=4500.0,
                order_id="ORD-001", timestamp=None):
    """Helper to create a standard order."""
    return Order(
        order_id=order_id,
        symbol=symbol,
        side=side,
        qty=qty,
        timestamp=timestamp or datetime(2026, 1, 15, 15, 0, tzinfo=timezone.utc),
        metadata={"reference_price": price},
    )


def _make_fill(symbol="MES", side=OrderSide.BUY, qty=1.0, fill_price=4502.25,
               expected_price=4500.0, slippage=2.25, commission=1.0,
               order_id="ORD-001", timestamp=None):
    """Helper to create a fill record."""
    return Fill(
        order_id=order_id,
        symbol=symbol,
        side=side,
        qty=qty,
        fill_price=fill_price,
        expected_price=expected_price,
        slippage=slippage,
        commission=commission,
        timestamp=timestamp or datetime(2026, 1, 15, 15, 0, tzinfo=timezone.utc),
    )


# ===========================================================
# SimAdapter Tests
# ===========================================================

class TestSimAdapter:
    """Basic SimAdapter execution tests."""

    def test_buy_deducts_cash(self, sim):
        order = _make_order(qty=1.0, price=4500.0)
        fill = sim.submit_order(order)
        assert fill.qty == 1.0
        assert sim.get_cash() < 100_000.0
        assert sim.get_position("MES") == 1.0

    def test_sell_returns_cash(self, sim):
        buy = _make_order(qty=1.0, price=4500.0)
        sim.submit_order(buy)
        sell = _make_order(side=OrderSide.SELL, qty=1.0, price=4510.0, order_id="ORD-002")
        sim.submit_order(sell)
        assert sim.get_position("MES") == 0.0
        assert sim.get_cash() > 0

    def test_insufficient_cash_rejected(self, sim):
        order = _make_order(qty=1000.0, price=4500.0)
        with pytest.raises(ExecutionError, match="Insufficient cash"):
            sim.submit_order(order)

    def test_insufficient_position_rejected(self, sim):
        sell = _make_order(side=OrderSide.SELL, qty=1.0, price=4500.0)
        with pytest.raises(ExecutionError, match="Insufficient position"):
            sim.submit_order(sell)

    def test_zero_qty_rejected(self, sim):
        order = _make_order(qty=0.0)
        with pytest.raises(ExecutionError, match="positive"):
            sim.submit_order(order)

    def test_fills_recorded_to_tape(self, sim):
        order = _make_order(qty=1.0, price=4500.0)
        sim.submit_order(order)
        assert sim.tape.fill_count == 1

    def test_slippage_applied(self, sim):
        """5 bps slippage on a buy should increase fill price."""
        order = _make_order(qty=1.0, price=4500.0)
        fill = sim.submit_order(order)
        expected_fill = 4500.0 * (1 + 5.0 / 10000.0)
        assert abs(fill.fill_price - expected_fill) < 0.01


# ===========================================================
# ExecutionSafety Tests
# ===========================================================

class TestExecutionSafety:
    """Test safety guardrails."""

    def test_position_limit_blocks(self):
        sim = SimAdapter(initial_cash=1_000_000_000.0, slippage_bps=0)
        config = SafetyConfig(max_position_size=10.0)
        safety = ExecutionSafety(sim, config)

        # Buy 10 — OK
        o1 = _make_order(qty=10.0, price=100.0, order_id="O1")
        safety.submit_order(o1)

        # Buy 1 more — should be blocked (would exceed 10)
        o2 = _make_order(qty=1.0, price=100.0, order_id="O2")
        with pytest.raises(ExecutionError, match="Position limit"):
            safety.submit_order(o2)

        assert safety.telemetry.orders_blocked_position == 1

    def test_duplicate_detection(self):
        sim = SimAdapter(initial_cash=1_000_000.0, slippage_bps=0)
        config = SafetyConfig(max_position_size=100.0)
        safety = ExecutionSafety(sim, config)

        o1 = _make_order(qty=1.0, price=100.0, order_id="O1")
        safety.submit_order(o1)

        # Same fingerprint within window → duplicate
        o2 = _make_order(qty=1.0, price=100.0, order_id="O2")
        with pytest.raises(ExecutionError, match="Duplicate"):
            safety.submit_order(o2)

        assert safety.telemetry.orders_blocked_duplicate == 1

    def test_calendar_cutoff_blocks(self):
        sim = SimAdapter(initial_cash=1_000_000.0, slippage_bps=0)
        config = SafetyConfig(enable_calendar_cutoff=True)

        # Mock calendar that always says "no new positions"
        mock_cal = MagicMock()
        mock_cal.no_new_positions_after.return_value = True

        safety = ExecutionSafety(sim, config, calendar=mock_cal)

        order = _make_order(qty=1.0, price=100.0)
        with pytest.raises(ExecutionError, match="Calendar cutoff"):
            safety.submit_order(order)

        assert safety.telemetry.orders_blocked_calendar == 1

    def test_calendar_allows_during_session(self):
        sim = SimAdapter(initial_cash=1_000_000.0, slippage_bps=0)
        config = SafetyConfig(
            enable_calendar_cutoff=True,
            max_position_size=100.0,
        )

        mock_cal = MagicMock()
        mock_cal.no_new_positions_after.return_value = False

        safety = ExecutionSafety(sim, config, calendar=mock_cal)

        order = _make_order(qty=1.0, price=100.0)
        fill = safety.submit_order(order)
        assert fill.qty == 1.0
        assert safety.telemetry.orders_blocked_calendar == 0

    def test_notional_limit_blocks(self):
        sim = SimAdapter(initial_cash=1_000_000.0, slippage_bps=0)
        config = SafetyConfig(
            max_notional_value=10_000.0,
            max_position_size=1000.0,
        )
        safety = ExecutionSafety(sim, config)

        order = _make_order(qty=10.0, price=5000.0, order_id="O1")
        with pytest.raises(ExecutionError, match="Notional limit"):
            safety.submit_order(order, reference_price=5000.0)

    def test_telemetry_report(self):
        sim = SimAdapter(initial_cash=1_000_000.0, slippage_bps=0)
        safety = ExecutionSafety(sim, SafetyConfig(max_position_size=100.0))

        order = _make_order(qty=1.0, price=100.0)
        safety.submit_order(order)

        telem = safety.get_telemetry()
        assert telem["orders_submitted"] == 1
        assert telem["orders_blocked_position"] == 0


# ===========================================================
# FillTape Tests
# ===========================================================

class TestFillTape:
    """Test append-only fill ledger and slippage drift."""

    def test_basic_record(self, tape):
        fill = _make_fill()
        result = tape.record(fill)
        assert tape.fill_count == 1
        # No alert for single fill below threshold
        assert result is None

    def test_immutable_view(self, tape):
        fill = _make_fill()
        tape.record(fill)
        fills_copy = tape.fills
        assert len(fills_copy) == 1
        # Modifying the copy should not affect the tape
        fills_copy.clear()
        assert tape.fill_count == 1

    def test_slippage_bps_calculation(self):
        fill = _make_fill(fill_price=4502.25, expected_price=4500.0)
        expected_bps = (4502.25 - 4500.0) / 4500.0 * 10000.0
        assert abs(fill.slippage_bps - expected_bps) < 0.01

    def test_drift_alert_when_threshold_exceeded(self):
        tape = FillTape(drift_alert_threshold_bps=10.0, rolling_window=3)

        # Record fills with high slippage
        for i in range(5):
            fill = _make_fill(
                fill_price=4600.0,
                expected_price=4500.0,
                slippage=100.0,
                order_id=f"O{i}",
            )
            result = tape.record(fill)

        # After enough fills with high slippage, should get alert
        assert result is not None
        assert result.drift_alert is True

    def test_telemetry_report(self, tape):
        fill1 = _make_fill(fill_price=4502.0, expected_price=4500.0, order_id="O1")
        fill2 = _make_fill(fill_price=4503.0, expected_price=4500.0, order_id="O2")
        tape.record(fill1)
        tape.record(fill2)

        telem = tape.get_telemetry()
        assert telem["total_fills"] == 2
        assert telem["symbols"] == ["MES"]

    def test_per_symbol_telemetry(self, tape):
        fill1 = _make_fill(symbol="MES", order_id="O1")
        fill2 = _make_fill(symbol="ES", order_id="O2")
        tape.record(fill1)
        tape.record(fill2)

        per_sym = tape.get_per_symbol_telemetry()
        assert "MES" in per_sym
        assert "ES" in per_sym
        assert per_sym["MES"]["fill_count"] == 1


# ===========================================================
# FlattenManager Tests
# ===========================================================

class TestFlattenManager:
    """Test Widowmaker flatten logic."""

    def test_flatten_triggered_by_calendar(self):
        sim = SimAdapter(initial_cash=100_000.0, slippage_bps=0)
        # Buy a position first
        order = _make_order(qty=1.0, price=4500.0)
        sim.submit_order(order)
        assert sim.get_position("MES") == 1.0

        # Mock calendar that says flatten
        mock_cal = MagicMock()
        mock_cal.should_flatten.return_value = True

        flatten_events = []
        fm = FlattenManager(
            sim, calendar=mock_cal,
            on_flatten=lambda e: flatten_events.append(e),
        )

        now = datetime(2026, 1, 15, 20, 46, tzinfo=timezone.utc)
        fills = fm.check_and_flatten(now, ["MES"], {"MES": 4500.0})

        assert len(fills) == 1
        assert sim.get_position("MES") == 0.0
        assert fm.flatten_count == 1
        assert len(flatten_events) == 1

    def test_no_flatten_when_calendar_says_no(self):
        sim = SimAdapter(initial_cash=100_000.0, slippage_bps=0)
        order = _make_order(qty=1.0, price=4500.0)
        sim.submit_order(order)

        mock_cal = MagicMock()
        mock_cal.should_flatten.return_value = False

        fm = FlattenManager(sim, calendar=mock_cal)
        now = datetime(2026, 1, 15, 18, 0, tzinfo=timezone.utc)
        fills = fm.check_and_flatten(now, ["MES"])

        assert len(fills) == 0
        assert sim.get_position("MES") == 1.0

    def test_no_flatten_when_flat(self):
        sim = SimAdapter(initial_cash=100_000.0, slippage_bps=0)

        mock_cal = MagicMock()
        mock_cal.should_flatten.return_value = True

        fm = FlattenManager(sim, calendar=mock_cal)
        now = datetime(2026, 1, 15, 20, 46, tzinfo=timezone.utc)
        fills = fm.check_and_flatten(now, ["MES"])

        assert len(fills) == 0
        assert fm.flatten_count == 0

    def test_telemetry(self):
        sim = SimAdapter(initial_cash=100_000.0, slippage_bps=5.0)
        order = _make_order(qty=1.0, price=4500.0)
        sim.submit_order(order)

        mock_cal = MagicMock()
        mock_cal.should_flatten.return_value = True

        fm = FlattenManager(sim, calendar=mock_cal)
        now = datetime(2026, 1, 15, 20, 46, tzinfo=timezone.utc)
        fm.check_and_flatten(now, ["MES"], {"MES": 4500.0})

        telem = fm.get_telemetry()
        assert telem["flatten_count"] == 1
        assert "MES" in telem["symbols_flattened"]


# ===========================================================
# Adapter Base Contract Tests
# ===========================================================

class TestAdapterContract:
    """Verify SimAdapter satisfies ExecutionAdapter contract."""

    def test_is_subclass(self):
        assert issubclass(SimAdapter, ExecutionAdapter)

    def test_implements_all_methods(self, sim):
        assert hasattr(sim, "submit_order")
        assert hasattr(sim, "cancel_order")
        assert hasattr(sim, "get_fills")
        assert hasattr(sim, "get_position")
        assert hasattr(sim, "get_cash")
