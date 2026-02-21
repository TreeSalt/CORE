import unittest
from datetime import datetime, timedelta, timezone

from antigravity_harness.execution.adapter_base import OrderIntent, OrderSide, OrderType
from antigravity_harness.execution.safety import ExecutionSafety, ExecutionSafetyConfig


class TestSafetyBreakers(unittest.TestCase):
    def setUp(self):
        config = ExecutionSafetyConfig(
            daily_loss_cap_usd=100.0,
            max_orders_per_sec=2,
            max_data_age_sec=1.0
        )
        self.guard = ExecutionSafety(config, None)
        self.intent = OrderIntent("MES", OrderSide.BUY, 1, OrderType.MARKET)

    def test_stale_data_breaker(self):
        """Verify that old data stops execution."""
        stale_ts = datetime.now(timezone.utc) - timedelta(seconds=2)
        ok, reason = self.guard.validate_intent(self.intent, 1000.0, stale_ts)
        self.assertFalse(ok)
        self.assertIn("STALE_DATA", reason)

        fresh_ts = datetime.now(timezone.utc)
        ok, reason = self.guard.validate_intent(self.intent, 1000.0, fresh_ts)
        self.assertTrue(ok)

    def test_rapid_fire_breaker(self):
        """Verify that too many orders in a second stops execution."""
        ts = datetime.now(timezone.utc)
        ok, reason = self.guard.validate_intent(self.intent, 1000.0, ts)
        self.assertTrue(ok)
        ok, reason = self.guard.validate_intent(self.intent, 1000.0, ts)
        self.assertTrue(ok)
        ok, reason = self.guard.validate_intent(self.intent, 1000.0, ts)
        self.assertFalse(ok)
        self.assertIn("RAPID_FIRE", reason)

    def test_drawdown_breaker(self):
        """Verify that exceeding daily loss cap stops execution."""
        ts = datetime.now(timezone.utc)
        self.guard.state.realized_pnl_usd = -50.0 
        ok, reason = self.guard.validate_intent(self.intent, 950.0, ts)
        self.assertTrue(ok)
        
        self.guard.state.realized_pnl_usd = -150.0
        ok, reason = self.guard.validate_intent(self.intent, 850.0, ts)
        self.assertFalse(ok)
        self.assertIn("Daily Loss Cap reached", reason)

if __name__ == "__main__":
    unittest.main()
