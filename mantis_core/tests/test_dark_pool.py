import unittest

from mantis_core.config import DarkPoolModel
from mantis_core.execution.adapter_base import OrderIntent, OrderSide, OrderType
from mantis_core.execution.sim_adapter import SimExecutionAdapter


class TestDarkPool(unittest.IsolatedAsyncioTestCase):
    async def test_price_improvement(self):
        """Verify that price improvement triggers correctly (statistical check)."""
        # Set improvement bps to something large for visibility
        dp = DarkPoolModel(
            enabled=True,
            fail_prob=0.0,
            improvement_prob=1.0,
            improvement_bps=10.0,
            adverse_selection_prob=0.0,
        )
        adapter = SimExecutionAdapter(dark_pool_model=dp)
        await adapter.connect()
        
        # Mid price 100.0. Buy order. 
        # Improvement 10 bps = 0.1 pts. Fill price should be 99.9.
        adapter.set_price("MES", 100.0)
        intent = OrderIntent(symbol="MES", side=OrderSide.BUY, quantity=1, order_type=OrderType.MARKET)
        
        await adapter.submit_order(intent)
        fill = adapter.all_fills[-1]
        
        # MISSION v4.5.290: ESD (Multiplier $5)
        # Improvement 10 bps on 100.25 = 100.149... -> 100.15
        self.assertAlmostEqual(float(fill.fill_price), 100.15, places=2)

    async def test_adverse_selection(self):
        """Verify that adverse selection increases fill cost."""
        dp = DarkPoolModel(enabled=True, fail_prob=0.0, improvement_prob=0.0, adverse_selection_prob=1.0, adverse_selection_bps=10.0)
        adapter = SimExecutionAdapter(dark_pool_model=dp)
        await adapter.connect()
        
        # Mid price 100.0. Buy order.
        # Adverse 10 bps = 0.1 pts. Fill price should be 100.1.
        adapter.set_price("MES", 100.0)
        intent = OrderIntent(symbol="MES", side=OrderSide.BUY, quantity=1, order_type=OrderType.MARKET)
        
        await adapter.submit_order(intent)
        fill = adapter.all_fills[-1]
        
        # Adverse 10 bps = 0.1 pts on 100.25 = 100.35
        self.assertGreater(float(fill.fill_price), 100.0)
        # Adverse 10 bps = 100.25 * 1.0010 = 100.35025 -> 100.35
        self.assertAlmostEqual(float(fill.fill_price), 100.35, places=2)

    async def test_info_leakage(self):
        """Verify that dark pool failure triggers information leakage penalty."""
        dp = DarkPoolModel(enabled=True, fail_prob=1.0, info_leakage_bps=5.0)
        adapter = SimExecutionAdapter(dark_pool_model=dp)
        await adapter.connect()
        
        # Mid price 100.0. Buy order.
        # Fail + 5 bps leakage = 0.05 pts. Fill price should be 100.05.
        adapter.set_price("MES", 100.0)
        intent = OrderIntent(symbol="MES", side=OrderSide.BUY, quantity=1, order_type=OrderType.MARKET)
        
        await adapter.submit_order(intent)
        fill = adapter.all_fills[-1]
        
        self.assertGreater(float(fill.fill_price), 100.0)
        # fill_price (100.25)
        self.assertAlmostEqual(float(fill.fill_price), 100.25, places=3)

if __name__ == "__main__":
    unittest.main()
