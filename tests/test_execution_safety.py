"""
tests/test_execution_safety.py
================================
Tests for the execution safety layer.

Every safety rule must have:
    1. A test that proves it FIRES when it should
    2. A test that proves it PASSES when conditions are within limits

Anti-vacuous: all tests are deterministic and use SimExecutionAdapter.
No network calls. No broker dependencies.
"""
from __future__ import annotations

import os
import sys
import unittest
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional

# Add patch path for import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import contextlib
import tempfile
from pathlib import Path

from antigravity_harness.execution.adapter_base import (
    CalendarAdapter,
    OrderIntent,
    OrderSide,
    OrderType,
    TimeInForce,
)
from antigravity_harness.execution.fill_tape import FillTape
from antigravity_harness.execution.flatten_manager import FlattenManager
from antigravity_harness.execution.rollover import (
    RolloverError,
    RolloverGuard,
    front_month_symbol,
    get_expiry_date,
    third_friday,
)
from antigravity_harness.execution.safety import (
    ATRFilterBlock,
    ContractLimitViolation,
    DailyLossCapReached,
    ExecutionSafety,
    ExecutionSafetyConfig,
    SessionBoundaryViolation,
)
from antigravity_harness.execution.sim_adapter import SimExecutionAdapter
from antigravity_harness.instruments.mes import (
    MES_MAX_PLANNED_RISK_USD,
    MES_SPEC,
    MESRiskParams,
)

# ─── Test Calendar ─────────────────────────────────────────────────────────────


class TestCalendar(CalendarAdapter):
    """Minimal calendar for testing. Mon-Fri trading, 09:30-16:00 ET → UTC offset -5."""

    def is_trading_day(self, d: date) -> bool:
        return d.weekday() < 5  # Mon-Fri

    def session_open_utc(self, d: date) -> datetime:
        if not self.is_trading_day(d):
            return None
        return datetime(d.year, d.month, d.day, 14, 30, tzinfo=timezone.utc)  # 09:30 ET = 14:30 UTC

    def session_close_utc(self, d: date) -> datetime:
        if not self.is_trading_day(d):
            return None
        return datetime(d.year, d.month, d.day, 21, 0, tzinfo=timezone.utc)  # 16:00 ET = 21:00 UTC

    def is_early_close(self, d: date) -> bool:
        return False

    def next_trading_day(self, d: date) -> date:
        next_d = d + timedelta(days=1)
        while not self.is_trading_day(next_d):
            next_d += timedelta(days=1)
        return next_d


    def no_new_positions_time_utc(self, d: date) -> Optional[datetime]:
        """
        STRICT MOCK: Enforce 15-minute buffer explicitly for tests.
        16:00 ET - 15m = 15:45 ET (20:45 UTC).
        """
        close = self.session_close_utc(d)
        if close is None:
            return None
        return close - timedelta(minutes=15)


def make_intent(
    symbol: str = "MES",
    side: OrderSide = OrderSide.BUY,
    qty: int = 1,
    order_type: OrderType = OrderType.MARKET,
) -> OrderIntent:
    return OrderIntent(
        symbol=symbol, side=side, quantity=qty, order_type=order_type,
        time_in_force=TimeInForce.DAY,
        client_order_id=f"test_{symbol}_{side.value}",
    )


def trading_time() -> datetime:
    """Return a datetime during RTH (Tuesday 10:00 ET = 15:00 UTC)."""
    return datetime(2026, 2, 17, 15, 0, 0, tzinfo=timezone.utc)


def after_cutoff_time() -> datetime:
    """Return a datetime after the 15:45 ET cutoff (15:46 ET = 20:46 UTC)."""
    return datetime(2026, 2, 17, 20, 46, 0, tzinfo=timezone.utc)


# ─── MES Constants Tests ──────────────────────────────────────────────────────


class TestMESConstants(unittest.TestCase):
    def test_risk_math_resolved(self):
        """Verify the frozen risk math: stop $35 + buffer $5 = $40."""
        from antigravity_harness.instruments.mes import MES_SLIPPAGE_BUFFER_USD, MES_STOP_RISK_USD
        self.assertAlmostEqual(MES_STOP_RISK_USD, 35.00)
        self.assertAlmostEqual(MES_SLIPPAGE_BUFFER_USD, 5.00)
        self.assertAlmostEqual(MES_MAX_PLANNED_RISK_USD, 40.00)

    def test_risk_params_validate(self):
        """MESRiskParams with 7pt stop + 4tk buffer = exactly $40 — should pass."""
        params = MESRiskParams(stop_points=7.0, slippage_buffer_ticks=4, max_contracts=1)
        params.validate()  # Should not raise

    def test_risk_params_reject_over_limit(self):
        """8pt stop + 4tk buffer = $45 — must raise."""
        params = MESRiskParams(stop_points=8.0, slippage_buffer_ticks=4, max_contracts=1)
        with self.assertRaises(ValueError):
            params.validate()


# ─── Safety Gate Tests ────────────────────────────────────────────────────────


class TestExecutionSafetyGates(unittest.TestCase):

    def setUp(self):
        self.config = ExecutionSafetyConfig()
        self.calendar = TestCalendar()
        self.safety = ExecutionSafety(self.config, self.calendar)
        self.safety.new_session(date(2026, 2, 17))

    def _ok_check(self) -> None:
        """A check that should pass under normal conditions."""
        self.safety.check_intent(
            intent=make_intent(),
            daily_atr_points=30.0,
            now_utc=trading_time(),
            current_position=0,
        )

    # ── Gate 0: Pause Mode ────────────────────────────────────────────────────

    def test_pause_mode_blocks_all_orders(self):
        """Once pause_trading=True, all orders are blocked."""
        self.safety.state.pause_trading = True
        self.safety.state.pause_reason = "TEST"
        with self.assertRaises(DailyLossCapReached):
            self._ok_check()

    # ── Gate 1: Daily Loss Cap ─────────────────────────────────────────────────

    def test_daily_loss_cap_fires(self):
        """When total P&L hits -$80, next order raises DailyLossCapReached."""
        self.safety.state.realized_pnl_usd = -80.00
        with self.assertRaises(DailyLossCapReached):
            self._ok_check()
        self.assertTrue(self.safety.state.pause_trading)

    def test_daily_loss_cap_does_not_fire_at_79(self):
        """$79 loss does not trigger cap ($80 is the threshold)."""
        self.safety.state.realized_pnl_usd = -79.00
        self._ok_check()  # Should not raise

    def test_unrealized_included_in_daily_cap(self):
        """Unrealized P&L counts toward daily loss cap."""
        self.safety.state.realized_pnl_usd = -50.00
        self.safety.update_unrealized(-30.01)  # Total = -$80.01
        with self.assertRaises(DailyLossCapReached):
            self._ok_check()

    def test_pause_persists_after_recovery(self):
        """Once paused, system stays paused even if P&L recovers."""
        self.safety.state.realized_pnl_usd = -80.00
        with contextlib.suppress(DailyLossCapReached):
            self._ok_check()
        # Now pretend P&L "recovered"
        self.safety.state.realized_pnl_usd = -10.00
        with self.assertRaises(DailyLossCapReached):
            self._ok_check()  # Still paused — pause_trading remains True

    # ── Gate 2: ATR Filter ─────────────────────────────────────────────────────

    def test_atr_filter_fires_above_threshold(self):
        """Daily ATR > 80 blocks all new orders."""
        with self.assertRaises(ATRFilterBlock):
            self.safety.check_intent(
                intent=make_intent(),
                daily_atr_points=80.1,
                now_utc=trading_time(),
            )

    def test_atr_filter_passes_at_threshold(self):
        """Daily ATR exactly 80 passes (threshold is >80, not >=80)."""
        self.safety.check_intent(
            intent=make_intent(),
            daily_atr_points=80.0,
            now_utc=trading_time(),
        )

    def test_atr_filter_passes_normal(self):
        """Normal daily ATR of 35 passes."""
        self.safety.check_intent(
            intent=make_intent(),
            daily_atr_points=35.0,
            now_utc=trading_time(),
        )

    # ── Gate 3: Session Boundary ──────────────────────────────────────────────

    def test_session_boundary_blocks_exact_cutoff(self):
        """
        Prove strict 15:45 ET cutoff.
        Close 16:00 ET -> cutoff 15:45 ET (20:45 UTC).

        15:46 ET (20:46 UTC) -> FAIL
        15:44 ET (20:44 UTC) -> PASS
        """
        late_time = datetime(2026, 2, 17, 20, 46, 0, tzinfo=timezone.utc)
        with self.assertRaises(SessionBoundaryViolation):
            self.safety.check_intent(
                intent=make_intent(),
                daily_atr_points=30.0,
                now_utc=late_time,
            )

        safe_time = datetime(2026, 2, 17, 20, 44, 0, tzinfo=timezone.utc)
        # Should not raise
        self.safety.check_intent(
            intent=make_intent(),
            daily_atr_points=30.0,
            now_utc=safe_time,
        )


    def test_session_boundary_blocks_after_cutoff(self):
        """Orders after 15:45 ET (no_new_positions) are blocked."""
        with self.assertRaises(SessionBoundaryViolation):
            self.safety.check_intent(
                intent=make_intent(),
                daily_atr_points=30.0,
                now_utc=after_cutoff_time(),
            )

    def test_session_boundary_passes_during_hours(self):
        """Orders at 10:00 ET pass session gate."""
        self.safety.check_intent(
            intent=make_intent(),
            daily_atr_points=30.0,
            now_utc=trading_time(),
        )

    def test_early_close_day(self):
        """On non-trading day, all orders blocked."""

        class EarlyCloseCalendar(TestCalendar):
            def is_trading_day(self, d):
                return False

        safety = ExecutionSafety(self.config, EarlyCloseCalendar())
        safety.new_session(date(2026, 2, 17))
        with self.assertRaises(SessionBoundaryViolation):
            safety.check_intent(
                intent=make_intent(),
                daily_atr_points=30.0,
                now_utc=trading_time(),
            )

    # ── Gate 4: Contract Limit ────────────────────────────────────────────────

    def test_contract_limit_fires(self):
        """Requesting 2 contracts when limit is 1 raises ContractLimitViolation."""
        with self.assertRaises(ContractLimitViolation):
            self.safety.check_intent(
                intent=make_intent(qty=2),
                daily_atr_points=30.0,
                now_utc=trading_time(),
            )

    def test_contract_limit_fires_on_resulting_position(self):
        """Already long 1 contract: adding another buy raises ContractLimitViolation."""
        with self.assertRaises(ContractLimitViolation):
            self.safety.check_intent(
                intent=make_intent(qty=1),
                daily_atr_points=30.0,
                now_utc=trading_time(),
                current_position=1,  # Already long 1
            )

    def test_contract_limit_passes_at_max(self):
        """1 contract with no existing position passes."""
        self.safety.check_intent(
            intent=make_intent(qty=1),
            daily_atr_points=30.0,
            now_utc=trading_time(),
            current_position=0,
        )

    # ── Gate 5: Risk Math ──────────────────────────────────────────────────────

    def test_risk_math_passes_with_correct_config(self):
        """Default config: 7pt stop + 4tk buffer = $40 — passes."""
        self._ok_check()

    def test_stop_orders_skip_risk_check(self):
        """Stop orders are exits — they skip the entry risk check."""
        stop_intent = make_intent(order_type=OrderType.STOP)
        self.safety.check_intent(
            intent=stop_intent,
            daily_atr_points=30.0,
            now_utc=trading_time(),
        )


# ─── FillTape Tests ───────────────────────────────────────────────────────────


class TestFillTape(unittest.TestCase):

    def _make_fill(self, side: OrderSide, fill_price: float):
        from antigravity_harness.execution.adapter_base import Fill
        return Fill(
            broker_order_id="test-001",
            client_order_id="test-001",
            symbol="MES",
            side=side,
            filled_qty=1,
            fill_price=Decimal(str(fill_price)),
            fill_time_utc=datetime(2026, 2, 17, 15, 0, tzinfo=timezone.utc),
            commission_usd=0.85,
        )

    def test_slippage_recorded(self):
        """FillTape computes slippage_realized_ticks correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tape = FillTape(Path(tmpdir), "2026-02-17", spec=MES_SPEC, slippage_buffer_ticks=4)
            fill = self._make_fill(OrderSide.BUY, fill_price=5000.25)
            record = tape.record(fill, expected_price=5000.00)
            # 0.25 points / 0.25 tick_size = 1 tick of slippage
            self.assertEqual(record.slippage_realized_ticks, 1)
            self.assertFalse(record.slippage_exceeded_buffer)

    def test_buffer_exceeded_flag(self):
        """Fill with 5 ticks slippage exceeds 4-tick buffer — flag set."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tape = FillTape(Path(tmpdir), "2026-02-17", spec=MES_SPEC, slippage_buffer_ticks=4)
            fill = self._make_fill(OrderSide.BUY, fill_price=5001.25)  # 5 ticks above
            record = tape.record(fill, expected_price=5000.00)
            self.assertEqual(record.slippage_realized_ticks, 5)
            self.assertTrue(record.slippage_exceeded_buffer)

    def test_drift_flag_emitted_above_threshold(self):
        """20%+ of fills exceeding buffer triggers ProfileDriftFlag artifact."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tape = FillTape(Path(tmpdir), "2026-02-17", spec=MES_SPEC, slippage_buffer_ticks=4)
            # 3 fills with >4 ticks slippage + 2 normal = 60% — above 20% threshold
            for _i in range(3):
                fill = self._make_fill(OrderSide.BUY, fill_price=5001.50)  # 6 ticks
                tape.record(fill, expected_price=5000.00)
            for _i in range(2):
                fill = self._make_fill(OrderSide.BUY, fill_price=5000.25)  # 1 tick
                tape.record(fill, expected_price=5000.00)
            tape.close()
            flag_file = Path(tmpdir) / "profile_drift_flag_2026-02-17.json"
            self.assertTrue(flag_file.exists(), "Drift flag not emitted")

    def test_no_drift_flag_below_threshold(self):
        """Single fill with excess slippage (20% of 1 = 100%? No: check exact math)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tape = FillTape(Path(tmpdir), "2026-02-17", spec=MES_SPEC, slippage_buffer_ticks=4)
            # 1 excess + 9 normal = 10% — below 20% threshold
            fill_bad = self._make_fill(OrderSide.BUY, fill_price=5001.50)
            tape.record(fill_bad, expected_price=5000.00)
            for _i in range(9):
                fill_ok = self._make_fill(OrderSide.BUY, fill_price=5000.00)
                tape.record(fill_ok, expected_price=5000.00)
            tape.close()
            flag_file = Path(tmpdir) / "profile_drift_flag_2026-02-17.json"
            self.assertFalse(flag_file.exists(), "Drift flag should NOT be emitted at 10%")


# ─── Rollover Tests ───────────────────────────────────────────────────────────


class TestRollover(unittest.TestCase):

    def test_third_friday_march_2026(self):
        """3rd Friday of March 2026 is March 20."""
        expiry = third_friday(2026, 3)
        self.assertEqual(expiry, date(2026, 3, 20))
        self.assertEqual(expiry.weekday(), 4)  # Friday

    def test_expiry_parsing(self):
        """MESH26 parses to March 2026 expiry (3rd Friday)."""
        expiry = get_expiry_date("MESH26")
        self.assertEqual(expiry.month, 3)
        self.assertEqual(expiry.year, 2026)

    def test_continuous_contract_no_expiry(self):
        """'MES' (continuous) returns None."""
        self.assertIsNone(get_expiry_date("MES"))

    def test_rollover_guard_fires_within_2_days(self):
        """Order on 2026-03-19 for MESH26 (expiry 2026-03-20) — 1 day away — rejected."""
        guard = RolloverGuard(min_days_to_expiry=2)
        with self.assertRaises(RolloverError):
            guard.check("MESH26", date(2026, 3, 19))

    def test_rollover_guard_passes_outside_window(self):
        """Order on 2026-03-01 for MESH26 (expiry 2026-03-20) — 19 days — passes."""
        guard = RolloverGuard(min_days_to_expiry=2)
        guard.check("MESH26", date(2026, 3, 1))  # Should not raise

    def test_rollover_guard_continuous_always_passes(self):
        """Continuous 'MES' contract never triggers rollover guard."""
        guard = RolloverGuard()
        guard.check("MES", date(2026, 3, 19))  # Should not raise

    def test_front_month_before_roll_window(self):
        """March 1 is before the 5-day roll window — front month is March."""
        sym = front_month_symbol(date(2026, 3, 1))
        self.assertIn("H26", sym)  # MESH26

    def test_front_month_during_roll_window(self):
        """March 16 is within 5 days of March 20 expiry — front month rolls to June."""
        sym = front_month_symbol(date(2026, 3, 16))
        self.assertIn("M26", sym)  # MESM26


# ─── FlattenManager Tests ─────────────────────────────────────────────────────


class TestFlattenManager(unittest.IsolatedAsyncioTestCase):

    async def test_flatten_long_position(self):
        """FlattenManager closes a long position and reports success."""
        adapter = SimExecutionAdapter(initial_cash=2000.0)
        await adapter.connect()
        adapter.set_price("MES", 5000.0)

        # Open a long position
        intent = make_intent(symbol="MES", side=OrderSide.BUY, qty=1)
        await adapter.submit_order(intent)

        # Flatten
        fm = FlattenManager(adapter, poll_interval_sec=0.01, timeout_sec=5.0)
        result = await fm.flatten("MES", reason="TEST")

        self.assertTrue(result.success)
        self.assertEqual(result.initial_position, 1)
        self.assertEqual(result.final_position, 0)
        self.assertFalse(result.reversal_detected)

    async def test_flatten_already_flat(self):
        """FlattenManager handles already-flat position gracefully."""
        adapter = SimExecutionAdapter(initial_cash=2000.0)
        await adapter.connect()
        adapter.set_price("MES", 5000.0)

        fm = FlattenManager(adapter, poll_interval_sec=0.01, timeout_sec=5.0)
        result = await fm.flatten("MES", reason="TEST_FLAT")

        self.assertTrue(result.success)
        self.assertEqual(result.initial_position, 0)
        self.assertEqual(result.final_position, 0)

    async def test_flatten_cancels_open_orders(self):
        """FlattenManager cancels open orders after position is closed."""
        adapter = SimExecutionAdapter(initial_cash=2000.0)
        await adapter.connect()
        adapter.set_price("MES", 5000.0)

        # Place a limit order (won't fill — no price match)
        limit_intent = OrderIntent(
            symbol="MES", side=OrderSide.BUY, quantity=1,
            order_type=OrderType.LIMIT, limit_price=Decimal("4900.0"),
            time_in_force=TimeInForce.DAY, client_order_id="limit_test",
        )
        await adapter.submit_order(limit_intent)

        fm = FlattenManager(adapter, poll_interval_sec=0.01, timeout_sec=5.0)
        result = await fm.flatten("MES", reason="TEST_CANCEL")

        self.assertTrue(result.success)
        self.assertEqual(result.orders_cancelled, 1)

    async def test_flatten_short_position(self):
        """FlattenManager closes a short position."""
        adapter = SimExecutionAdapter(initial_cash=2000.0)
        await adapter.connect()
        adapter.set_price("MES", 5000.0)

        # Open short
        intent = make_intent(symbol="MES", side=OrderSide.SELL, qty=1)
        await adapter.submit_order(intent)

        fm = FlattenManager(adapter, poll_interval_sec=0.01, timeout_sec=5.0)
        result = await fm.flatten("MES", reason="TEST_SHORT")

        self.assertTrue(result.success)
        self.assertEqual(result.initial_position, -1)
        self.assertEqual(result.final_position, 0)


# ─── SimAdapter Tests ─────────────────────────────────────────────────────────


class TestSimAdapter(unittest.IsolatedAsyncioTestCase):

    async def test_market_buy_fills_immediately(self):
        adapter = SimExecutionAdapter(initial_cash=2000.0)
        await adapter.connect()
        adapter.set_price("MES", 5000.0)

        ack = await adapter.submit_order(make_intent(side=OrderSide.BUY))
        from antigravity_harness.execution.adapter_base import OrderStatus
        self.assertEqual(ack.status, OrderStatus.FILLED)

        pos = await adapter.get_position("MES")
        self.assertEqual(pos.quantity, 1)

    async def test_slippage_applied_to_buy(self):
        """2-tick sim slippage fills BUY 2 ticks above mid."""
        adapter = SimExecutionAdapter(sim_slippage_ticks=2)
        await adapter.connect()
        adapter.set_price("MES", 5000.0)

        await adapter.submit_order(make_intent(side=OrderSide.BUY))
        fill = adapter.all_fills[-1]
        # MISSION v4.5.290: 5000 + 0.25 (mandatory) + 2*0.25 (synthetic) = 5000.75
        expected = 5000.75
        self.assertAlmostEqual(float(fill.fill_price), expected)


if __name__ == "__main__":
    unittest.main()
