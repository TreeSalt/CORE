---
DOMAIN: 06_BENCHMARKING
MODEL: qwen3.5:4b
TIER: sprinter
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

```python
import unittest
import numpy as np
from unittest.mock import Mock, MagicMock, patch
import pytest
from mantis.core.regime_detector import RegimeDetector
from mantis.core.trend_signal import TrendSignal
from mantis.core.position_sizer import PositionSizer
from mantis.core.alpaca_harness import AlpacaHarness

class TestRegimeDetector(unittest.TestCase):
    def setUp(self):
        self.detector = RegimeDetector()
    
    def test_up_trending_detected(self):
        # Generate synthetic data for uptrend
        np.random.seed(42)
        data = np.array([1.0, 1.5, 2.0, 2.5])
        self.detector.calculate(data)
        self.assertTrue(self.detector.is_up, "Expected uptrend detected")
    
    def test_down_trending_detected(self):
        # Generate synthetic data for downtrend
        np.random.seed(42)
        data = np.array([3.0, 2.5, 2.0, 1.5])
        self.detector.calculate(data)
        self.assertTrue(self.detector.is_down, "Expected downtrend detected")
    
    def test_volatile_detected(self):
        # Generate synthetic data for high volatility
        np.random.seed(42)
        data = np.array([1.0, 1.5, 0.9, 1.8])
        self.detector.calculate(data)
        self.assertTrue(self.detector.is_volatile, "Volatile state expected")
    
    def test_min_bars_enforced(self):
        # Simulate min bar check by ensuring calculate handles empty/small datasets
        empty_data = np.array([])
        # Check if it raises or returns specific default on insufficient data
        with self.assertRaises(AssertionError): 
            self.detector.calculate(empty_data)
    
    def test_confidence_range(self):
        np.random.seed(42)
        data = np.array([1.0, 1.5, 2.0])
        result = self.detector.get_confidence()
        # Check confidence within range 0.0 to 1.0 (example logic)
        self.assertLessEqual(result, 1.0)
        self.assertGreaterEqual(result, 0.0)
    
    def test_fields_populated(self):
        np.random.seed(42)
        data = np.array([1.0, 1.5, 2.0])
        self.detector.calculate(data)
        self.assertTrue(hasattr(self.detector, 'is_up'), "Field is_up not populated")
        self.assertTrue(hasattr(self.detector, 'is_down'), "Field is_down not populated")

class TestTrendSignal(unittest.TestCase):
    def setUp(self):
        self.signal = TrendSignal()
    
    def test_buy_in_uptrend(self):
        data = np.array([1.0, 2.0, 3.0])
        # Mock detector to indicate uptrend
        mock_detector = MagicMock()
        mock_detector.is_up = True
        self.signal.attach_detector(mock_detector)
        signal = self.signal.get_signal(data)
        self.assertEqual(signal, "BUY", "Expected buy signal in uptrend")
    
    def test_hold_in_ranging(self):
        data = np.array([1.0, 1.1, 1.0]) # Range like
        mock_detector = MagicMock()
        mock_detector.is_up = False
        mock_detector.is_down = False
        self.signal.attach_detector(mock_detector)
        signal = self.signal.get_signal(data)
        self.assertEqual(signal, "HOLD", "Expected hold in ranging")
    
    def test_exit_on_regime_shift(self):
        # Simulate regime shift causing exit
        mock_detector = MagicMock()
        mock_detector.is_up = True
        # Force a shift condition
        signal = self.signal.get_signal(np.array([10, 20]), regime_shift=True)
        self.assertEqual(signal, "EXIT", "Expected exit on regime shift")
    
    def test_stop_loss_set(self):
        self.signal.set_stop_loss(0.05)
        mock_detector = MagicMock()
        mock_detector.price = 100
        mock_detector.change = -0.50 # Loss > SL
        result = self.signal.is_stop_triggered(mock_detector)
        self.assertTrue(result, "Stop loss should trigger on significant loss")
    
    def test_never_long_in_downtrend(self):
        data = np.array([10, 9, 8])
        mock_detector = MagicMock()
        mock_detector.is_up = False
        mock_detector.is_down = True
        self.signal.attach_detector(mock_detector)
        signal = self.signal.get_signal(data)
        self.assertNotIn(signal, "BUY", "Should never go long in downtrend")

class TestPositionSizer(unittest.TestCase):
    def setUp(self):
        self.sizer = PositionSizer()
    
    def test_basic_calc(self):
        equity = 10000
        risk_percent = 0.05
        result = self.sizer.calculate_position(equity, risk_percent)
        # Basic calc should return positive float
        self.assertGreater(result, 0)
    
    def test_zero_equity_raises(self):
        with self.assertRaises(ValueError):
            self.sizer.calculate_position(0, 0.05)
    
    def test_no_max_cap_enforced(self):
        result = self.sizer.calculate_position(10000, 0.05)
        # If no hard cap exists in logic, should return calculated amount
        self.assertIsNotNone(result)

class TestAlpacaHarness(unittest.TestCase):
    def setUp(self):
        self.harness = AlpacaHarness()
        
    @patch('alpaca.api.rest.AlpacaRestAPI')
    def test_market_data_retrieval(self, mock_api_class):
        mock_instance = MagicMock()
        mock_api_class.return_value = mock_instance
        
        # Setup mock data
        mock_stock_price = 100.0
        
        with patch('builtins.range'): # or similar if range is used for loop

    def test_order_placement(self, mock_alpaca):
        order = Mock()
        order.is_open = False
        
        mock_alpaca.place_order.return_value = order
        
        result = self.harness.buy(stock_symbol='AAPL', qty=10)
        
        # Check if place_order was called
        mock_alpaca.place_order.assert_called_once()

    def test_balance_check(self, mock_alpaca):
        mock_account = MagicMock()
        mock_account.get_balance.return_value = 5000
        
        result = self.harness.check_balance()
        
        mock_account.get_balance.assert_called_once()
```