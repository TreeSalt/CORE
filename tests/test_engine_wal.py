import tempfile
import unittest
from pathlib import Path

import pandas as pd

from antigravity_harness.engine import SimulatedAccount
from antigravity_harness.wal import WriteAheadLog


class TestEngineWAL(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.test_dir.name) / "test_wal.db"
        self.wal = WriteAheadLog(self.db_path)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_buy_intent_logging(self):
        """Verify BUY intents are logged and committed."""
        account = SimulatedAccount(10000.0, 0.0, False, wal=self.wal)

        # Execute Buy
        account.buy(
            price=100.0,
            timestamp=pd.Timestamp("2024-01-01"),
            volume=1000,
            limit_pct=1.0,  # Allow full fill
        )

        # Verify WAL
        self.wal.cursor.execute("SELECT * FROM intent_log")
        rows = self.wal.cursor.fetchall()
        self.assertEqual(len(rows), 1)

        # Row structure: id, timestamp, intent_type, payload, status
        _, _, intent_type, payload, status = rows[0]
        self.assertEqual(intent_type, "BUY")
        self.assertEqual(status, "COMMITTED")
        self.assertIn('"symbol": "SIM"', payload)
        # Qty might be 100 or 100.0 depending on json serialization
        self.assertTrue('"qty": 100' in payload)

    def test_sell_intent_logging(self):
        """Verify SELL intents are logged and committed."""
        account = SimulatedAccount(10000.0, 0.0, False, wal=self.wal)
        # Setup position
        account.cash = 0.0
        account.qty = 100.0
        account.entry_price = 100.0
        account.entry_time = pd.Timestamp("2024-01-01")

        # Execute Sell
        account.sell(
            price=110.0, timestamp=pd.Timestamp("2024-01-02"), reason="take_profit", volume=1000, limit_pct=1.0
        )

        # Verify WAL
        self.wal.cursor.execute("SELECT * FROM intent_log")
        rows = self.wal.cursor.fetchall()
        self.assertEqual(len(rows), 1)

        _, _, intent_type, payload, status = rows[0]
        self.assertEqual(intent_type, "SELL")
        self.assertEqual(status, "COMMITTED")
        self.assertIn('"reason": "take_profit"', payload)

    def test_crash_recovery_simulation(self):
        """Simulate a crash during BUY execution (Mocking PENDING state)."""
        # Manually insert a PENDING intent
        self.wal.log_intent("BUY", {"symbol": "SIM", "qty": 50})

        # Verify it exists as PENDING
        self.wal.cursor.execute("SELECT status FROM intent_log WHERE status='PENDING'")
        self.assertEqual(len(self.wal.cursor.fetchall()), 1)

        # Recovery (The Phoenix Protocol)
        # In a real scenario, the startup logic would read this.
        # Here we just verify the WAL exposes it via recover() logic (or similar query)
        self.wal.cursor.execute("SELECT * FROM intent_log WHERE status='PENDING'")
        crashes = self.wal.cursor.fetchall()
        self.assertEqual(len(crashes), 1)
        print(f"Verified PENDING intent exists for recovery: {crashes[0]}")


if __name__ == "__main__":
    unittest.main()
