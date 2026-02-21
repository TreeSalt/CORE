import time
import unittest

from antigravity_harness.config import LatencyModel
from antigravity_harness.execution.adapter_base import OrderIntent, OrderSide, OrderType
from antigravity_harness.execution.sim_adapter import SimExecutionAdapter


class TestLatencyDynamic(unittest.IsolatedAsyncioTestCase):
    async def test_base_latency(self):
        """Verify that base latency is applied even without market factors."""
        lm = LatencyModel(base_ms=100)
        adapter = SimExecutionAdapter(latency_model=lm)
        await adapter.connect()
        
        intent = OrderIntent(symbol="MES", side=OrderSide.BUY, quantity=1, order_type=OrderType.MARKET)
        adapter.set_price("MES", 5000.0)
        
        start = time.time()
        await adapter.submit_order(intent)
        elapsed = (time.time() - start) * 1000
        
        self.assertGreaterEqual(elapsed, 100)
        self.assertLess(elapsed, 200) # Tolerance for local execution

    async def test_volatility_scaling(self):
        """Verify that high volatility increases execution delay."""
        lm = LatencyModel(base_ms=50, vol_scaling_ms=10)
        adapter = SimExecutionAdapter(latency_model=lm)
        await adapter.connect()
        
        intent = OrderIntent(symbol="MES", side=OrderSide.BUY, quantity=1, order_type=OrderType.MARKET)
        
        # High volatility case (e.g. 20.0 vol)
        adapter.set_price("MES", 5000.0, volatility=20.0)
        # Expected delay = 50 + 20*10 = 250ms
        
        start = time.time()
        await adapter.submit_order(intent)
        elapsed = (time.time() - start) * 1000
        
        self.assertGreaterEqual(elapsed, 250)

    async def test_volume_scaling(self):
        """Verify that large orders relative to volume increase delay."""
        lm = LatencyModel(base_ms=50, size_scaling_ms=1000)
        adapter = SimExecutionAdapter(latency_model=lm)
        await adapter.connect()
        
        # Order for 100 contracts on 1000 volume bar
        intent = OrderIntent(symbol="MES", side=OrderSide.BUY, quantity=100, order_type=OrderType.MARKET)
        adapter.set_price("MES", 5000.0, volume=1000.0)
        # Expected delay = 50 + (100/1000)*1000 = 150ms
        
        start = time.time()
        await adapter.submit_order(intent)
        elapsed = (time.time() - start) * 1000
        
        self.assertGreaterEqual(elapsed, 150)

if __name__ == "__main__":
    unittest.main()
