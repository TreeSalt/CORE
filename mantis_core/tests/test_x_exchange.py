import tempfile
import unittest
from decimal import Decimal

from mantis_core.config import DarkPoolModel
from mantis_core.execution.adapter_base import Fill, OrderIntent, OrderSide, OrderType
from mantis_core.execution.fill_tape import FillTape
from mantis_core.execution.sim_adapter import SimExecutionAdapter


class TestCrossExchangeForensics(unittest.IsolatedAsyncioTestCase):

    async def test_dark_pool_venue_routing(self):
        """Verify that Fills carry exact venue tags mapping to simulated venue logic."""
        
        # Test 1: Forced Improvement (Always DARK_POOL)
        dp_model_1 = DarkPoolModel(
            enabled=True,
            fail_prob=0.0,
            improvement_prob=1.0, 
            improvement_bps=2.0,
            adverse_selection_prob=0.0,
            adverse_selection_bps=0.0,
            info_leakage_bps=0.0
        )
        
        adapter1 = SimExecutionAdapter(dark_pool_model=dp_model_1)
        adapter1._current_prices["MES"] = 5000.0
        
        intent1 = OrderIntent(
            symbol="MES",
            side=OrderSide.BUY,
            quantity=1,
            order_type=OrderType.MARKET
        )
        await adapter1.submit_order(intent1)
        
        self.assertEqual(len(adapter1._fills), 1)
        fill1: Fill = adapter1._fills[0]
        self.assertEqual(fill1.venue, "DARK_POOL")
        
        # Test 2: Forced Failure/Leakage (Always routes back to LIT_EXCHANGE)
        dp_model_2 = DarkPoolModel(
            enabled=True,
            fail_prob=1.0, # 100% fail
            improvement_prob=0.0,
            improvement_bps=0.0,
            adverse_selection_prob=0.0,
            adverse_selection_bps=0.0,
            info_leakage_bps=1.0
        )
        
        adapter2 = SimExecutionAdapter(dark_pool_model=dp_model_2)
        adapter2._current_prices["MES"] = 5000.0
        await adapter2.submit_order(intent1)
        
        fill2: Fill = adapter2._fills[0]
        self.assertEqual(fill2.venue, "LIT_EXCHANGE")
        
    def test_fill_tape_venue_serialization(self):
        """Verify that FillTape CSV permanently writes the venue string."""
        import pathlib
        from datetime import datetime, timezone
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tape = FillTape(output_dir=pathlib.Path(tmpdir), session_date="2026-02-21")
            
            fill_mock = Fill(
                broker_order_id="123",
                client_order_id="abc",
                symbol="MES",
                side=OrderSide.BUY,
                filled_qty=3,
                fill_price=Decimal("4999.00"),
                fill_time_utc=datetime.now(tz=timezone.utc),
                commission_usd=1.24,
                venue="DARK_POOL"
            )
            
            tape.record(fill_mock, expected_price=5000.0)
            csv_path = tape.close()
            
            import csv
            with open(csv_path, "r") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["venue"], "DARK_POOL")

if __name__ == "__main__":
    unittest.main()
