import unittest

from mantis_core.execution.adapter_base import OrderIntent, OrderSide, OrderType
from mantis_core.execution.fiduciary import FiduciaryBridge
from mantis_core.execution.sim_adapter import SimExecutionAdapter


class TestFiduciaryBridge(unittest.IsolatedAsyncioTestCase):
    async def test_clamping_logic(self):
        # 1. Setup base adapter (Simulation)
        base = SimExecutionAdapter(initial_cash=10000.0)
        await base.connect()
        
        # 2. Wrap with Fiduciary Bridge (Max Qty = 2)
        bridge = FiduciaryBridge(base, max_qty=2)
        
        # 3. Submit order that exceeds limit (Qty = 100)
        intent = OrderIntent(
            symbol="BTC-USD",
            side=OrderSide.BUY,
            quantity=100,
            order_type=OrderType.MARKET,
            client_order_id="test-123"
        )
        
        # 4. submission
        await bridge.submit_order(intent)
        
        # 5. Verify clamping
        # The base adapter should only have a position of 2
        pos = await base.get_position("BTC-USD")
        self.assertEqual(pos.quantity, 2)
        
        # All fills should also show qty 2
        fills = base.all_fills
        self.assertEqual(len(fills), 1)
        self.assertEqual(fills[0].filled_qty, 2)
        
        await base.disconnect()

    async def test_under_limit_passthrough(self):
        base = SimExecutionAdapter(initial_cash=10000.0)
        await base.connect()
        bridge = FiduciaryBridge(base, max_qty=5)
        
        # Submit order under limit (Qty = 3)
        intent = OrderIntent(
            symbol="ETH-USD",
            side=OrderSide.BUY,
            quantity=3,
            order_type=OrderType.MARKET,
            client_order_id="test-456"
        )
        
        await bridge.submit_order(intent)
        
        pos = await base.get_position("ETH-USD")
        self.assertEqual(pos.quantity, 3)
        
        await base.disconnect()

if __name__ == "__main__":
    unittest.main()
