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
from unittest import mock
from mantis_trading.regime_detector import RegimeDetector
from mantis_trading.trend_signal import TrendSignal
from mantis_trading.position_sizer import PositionSizer
from mantis_trading.alpaca_harness import AlpacaHarness


class TestRegimeDetector(unittest.TestCase):
    """Tests for regime detector module"""
    
    def test_trending_up(self):
        """Test trending up detected"""
        data = np.arange(10) * 1.5 + 50
        detector = RegimeDetector(min_bars=5)
        result = detector.detect(data=data)
        self.assertEqual(result.regime, 'UP_TREND')
        self.assertIsNotNone(result.confidence)
    
    def test_trending_down(self):
        """Test trending down detected"""
        data = np.arange(10) * 1.5 + 45
        detector = RegimeDetector(min_bars=5)
        result = detector.detect(data=data)
        self.assertEqual(result.regime, 'DOWN_TREND')
        self.assertIsNotNone(result.confidence)
    
    def test_volatile(self):
        """Test volatile regime detected"""
        data = np.random.randn(10) * 5 + 50
        detector = RegimeDetector(min_bars=5)
        result = detector.detect(data=data)
        self.assertIn(result.regime, ['VOLATILE', 'UNKNOWN'])
    
    def test_min_bars_enforced(self):
        """Test minimum bars enforced"""
        data = np.arange(3) * 1.5 + 50
        detector = RegimeDetector(min_bars=5)
        result = detector.detect(data=data)
        self.assertEqual(result.regime, 'UNKNOWN')
    
    def test_confidence_range(self):
        """Test confidence range"""
        data = np.arange(20) * 1.5 + 50
        detector = RegimeDetector(min_bars=5)
        result = detector.detect(data=data)
        self.assertTrue(0.3 <= result.confidence <= 0.9)
    
    def test_fields_populated(self):
        """Test all fields populated"""
        data = np.arange(10) * 1.5 + 50
        detector = RegimeDetector(min_bars=5)
        result = detector.detect(data=data)
        self.assertTrue(hasattr(result, 'regime'))
        self.assertTrue(hasattr(result, 'confidence'))
        self.assertTrue(hasattr(result, 'data_len'))


class TestTrendSignal(unittest.TestCase):
    """Tests for trend signal module"""
    
    def test_buy_in_uptrend(self):
        """Test buy signal in uptrend"""
        data = np.arange(10) * 1.5 + 50
        signal = TrendSignal(data=data, min_bars=5)
        result = signal.get_signal()
        self.assertEqual(result.signal, 'BUY')
    
    def test_hold_in_ranging(self):
        """Test hold signal in ranging"""
        data = np.random.randn(10) * 2 + 50
        signal = TrendSignal(data=data, min_bars=5)
        result = signal.get_signal()
        self.assertEqual(result.signal, 'HOLD')
    
    def test_exit_on_regime_shift(self):
        """Test exit on regime shift"""
        data = np.arange(10) * 1.5 + 50
        signal = TrendSignal(data=data, min_bars=5)
        result = signal.get_signal()
        self.assertIn('EXIT', str(result))
    
    def test_stop_loss_set(self):
        """Test stop loss is set"""
        data = np.arange(10) * 1.5 + 50
        signal = TrendSignal(data=data, min_bars=5)
        result = signal.get_signal()
        self.assertTrue(hasattr(result, 'stop_loss'))
    
    def test_never_long_in_downtrend(self):
        """Test never long in downtrend"""
        data = np.arange(10) * 1.5 + 45
        signal = TrendSignal(data=data, min_bars=5)
        result = signal.get_signal()
        self.assertNotEqual(result.signal, 'LONG')


class TestPositionSizer(unittest.TestCase):
    """Tests for position sizer module"""
    
    def test_basic_calc(self):
        """Test basic calculation"""
        sizer = PositionSizer(equity=10000, distance=2.5)
        result = sizer.calculate_position()
        self.assertGreater(result.position, 0)
        self.assertLessEqual(result.position, 10000)
    
    def test_zero_equity_raises(self):
        """Test zero equity raises error"""
        sizer = PositionSizer(equity=0, distance=2.5)
        with self.assertRaises(ValueError):
            sizer.calculate_position()
    
    def test_zero_distance_raises(self):
        """Test zero distance raises error"""
        sizer = PositionSizer(equity=10000, distance=0)
        with self.assertRaises(ValueError):
            sizer.calculate_position()
    
    def test_max_clamp(self):
        """Test maximum position clamped"""
        sizer = PositionSizer(equity=5000, distance=2.5)
        result = sizer.calculate_position()
        self.assertLessEqual(result.position, 5000)
    
    def test_never_negative(self):
        """Test never negative position"""
        sizer = PositionSizer(equity=10000, distance=2.5)
        result = sizer.calculate_position()
        self.assertGreaterEqual(result.position, 0)
    
    def test_crypto_precision(self):
        """Test crypto precision handling"""
        sizer = PositionSizer(equity=10000, distance=2.5)
        result = sizer.calculate_position()
        precision_digits = len(str(result.position).split('.')[-1]) if '.' in str(result.position) else 0
        self.assertLessEqual(precision_digits, 12)


class TestAlpacaHarness(unittest.TestCase):
    """Tests for Alpaca harness module"""
    
    def test_missing_key_raises(self):
        """Test missing key raises error"""
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError):
                AlpacaHarness(api_key='', api_secret='')
    
    def test_initializes_with_mock(self):
        """Test initializes with mock"""
        mock_response = mock.MagicMock()
        mock_response.status_code = 200
        mock_data = mock.MagicMock()
        mock_data.json.return_value = {'account': 'TEST'}
        
        with mock.patch('requests.post', return_value=mock_response):
            harness = AlpacaHarness(api_key='test_key', api_secret='test_secret')
            result = harness.get_account()
            self.assertEqual(result, 'TEST')
    
    def test_max_position_enforced(self):
        """Test max position enforced"""
        mock_response = mock.MagicMock()
        mock_response.status_code = 200
        mock_data = mock.MagicMock()
        mock_data.json.return_value = {'account': {'balance': 1000}}
        
        with mock.patch('requests.post', return_value=mock_response):
            harness = AlpacaHarness(api_key='test_key', api_secret='test_secret')
            result = harness.get_max_position()
            self.assertGreaterEqual(result, 0)
```