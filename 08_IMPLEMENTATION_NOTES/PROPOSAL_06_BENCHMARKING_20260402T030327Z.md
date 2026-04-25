---
DOMAIN: 06_BENCHMARKING
MODEL: qwen3.5:4b
TIER: sprinter
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

```python
import unittest
from numpy.testing import assert_array_equal
import os
import numpy as np


class TestRegimeDetector(unittest.TestCase):
    def test_trending_up_detected(self):
        detector = RegimeDetector(min_bars=50, volatility_threshold=0.02)
        data = np.linspace(100, 200, 100)
        signal = TrendSignalGenerator()
        signal.generate(data=data)
        result = detector.detect_signal(signal=signal)
        self.assertTrue(result['trending_up'], "Expected trending_up for upward movement")

    def test_trending_down_detected(self):
        detector = RegimeDetector(min_bars=50, volatility_threshold=0.02)
        data = np.linspace(1000, 900, 100)
        signal = TrendSignalGenerator()
        signal.generate(data=data)
        result = detector.detect_signal(signal=signal)
        self.assertTrue(result['trending_down'], "Expected trending_down for downward movement")

    def test_volatile_detected(self):
        detector = RegimeDetector(min_bars=25, volatility_threshold=0.01)
        data = np.random.randn(100) * 5
        signal = TrendSignalGenerator()
        signal.generate(data=data)
        result = detector.detect_signal(signal=signal)
        self.assertTrue(result['volatile'], "Expected volatile detection for high variance data")

    def test_min_bars_enforced(self):
        detector = RegimeDetector(min_bars=100, volatility_threshold=0.02)
        data = np.linspace(50, 150, 49)
        signal = TrendSignalGenerator()
        signal.generate(data=data)
        with self.assertRaises(AssertionError):
            detector.detect_signal(signal=signal)

    def test_confidence_range(self):
        detector = RegimeDetector(min_bars=30, volatility_threshold=0.015)
        data = np.linspace(100, 250, 80)
        signal = TrendSignalGenerator()
        signal.generate(data=data)
        result = detector.detect_signal(signal=signal)
        self.assertIn('confidence', result.keys(), "Result should contain confidence field")
        self.assertGreater(result['confidence'], 0.6, "Confidence should be above 0.6")

    def test_fields_populated(self):
        detector = RegimeDetector(min_bars=25, volatility_threshold=0.01)
        data = np.linspace(100, 300, 100)
        signal = TrendSignalGenerator()
        signal.generate(data=data)
        result = detector.detect_signal(signal=signal)
        self.assertIn('trend', result.keys(), "Result should contain trend field")
        self.assertIn('direction', result.keys(), "Result should contain direction field")


class TestTrendSignal(unittest.TestCase):
    def test_buy_in_uptrend(self):
        signal_gen = TrendSignalGenerator()
        data = np.linspace(100, 200, 50)
        signal = signal_gen.generate(data=data)
        result = signal.get_entry_signal(signal=signal)
        self.assertIn('buy', result.keys(), "Result should contain entry signals")

    def test_hold_in_ranging(self):
        signal_gen = TrendSignalGenerator()
        data = np.random.randn(50) * 10 + 100
        signal = signal_gen.generate(data=data)
        result = signal.get_entry_signal(signal=signal)
        self.assertIn('hold', result.keys(), "Result should contain hold signals for ranging market")

    def test_exit_on_regime_shift(self):
        signal_gen = TrendSignalGenerator()
        data = np.linspace(100, 200, 30) + np.linspace(200, 150, 30)
        signal = signal_gen.generate(data=data)
        result = signal.get_entry_signal(signal=signal)
        self.assertIn('exit', result.keys(), "Result should contain exit signals")

    def test_stop_loss_set(self):
        signal_gen = TrendSignalGenerator()
        data = np.linspace(100, 200, 40)
        signal = signal_gen.generate(data=data)
        result = signal.get_entry_signal(signal=signal)
        self.assertIn('stop_loss', result.keys(), "Result should contain stop loss")

    def test_never_long_in_downtrend(self):
        signal_gen = TrendSignalGenerator()
        data = np.linspace(1000, 800, 50)
        signal = signal_gen.generate(data=data)
        result = signal.get_entry_signal(signal=signal)
        self.assertNotIn('long', result.keys(), "Should not generate long signals in downtrend")


class TestPositionSizer(unittest.TestCase):
    def test_basic_calc(self):
        sizer = PositionSizer()
        risk = 1000.0
        equity = 100000.0
        position_size = sizer.calculate_position(risk=risk, equity=equity)
        self.assertGreaterEqual(position_size, 0, "Position size should be non-negative")

    def test_zero_equity_raises(self):
        sizer = PositionSizer()
        equity = 0.0
        with self.assertRaises(ValueError):
            sizer.calculate_position(risk=1000.0, equity=equity)

    def test_zero_distance_raises(self):
        sizer = PositionSizer()
        risk = 0.0
        equity = 100000.0
        with self.assertRaises(ValueError):
            sizer.calculate_position(risk=risk, equity=equity)

    def test_max_clamp(self):
        sizer = PositionSizer(max_position=5000)
        risk = 100000.0
        equity = 200000.0
        position_size = sizer.calculate_position(risk=risk, equity=equity)
        self.assertLessEqual(position_size, 5000, "Position should be clamped to max")

    def test_never_negative(self):
        sizer = PositionSizer()
        risk = 1000.0
        equity = -1000000.0
        position_size = sizer.calculate_position(risk=risk, equity=equity)
        self.assertGreaterEqual(position_size, 0, "Position size should never be negative")

    def test_crypto_precision(self):
        sizer = PositionSizer()
        risk = 100.0
        equity = 10000.0
        position_size = sizer.calculate_position(risk=risk, equity=equity)
        decimals = len(str(position_size).split('.')[1]) if '.' in str(position_size) else 0
        self.assertGreaterEqual(decimals, 8, "Position size should maintain crypto precision")


class TestAlpacaHarness(unittest.TestCase):
    def test_missing_key_raises(self):
        harness = AlpacaHarness(api_key=os.environ.get("ALPACA_API_KEY", ""))
        with self.assertRaises(KeyError):
            _ = harness.get_market_data()

    def test_initializes_with_mock(self):
        harness = AlpacaHarness(api_key=os.environ.get("ALPACA_API_KEY", ""))
        mock_response = {'market_data': {}}
        with unittest.mock.patch.object(harness, '_get_market_data', return_value=mock_response) as mock:
            result = harness.get_market_data()
            mock.assert_called_once()
            self.assertEqual(result, mock_response)

    def test_max_position_enforced(self):
        harness = AlpacaHarness(api_key=os.environ.get("ALPACA_API_KEY", ""))
        max_pos = 10000.0
        harness._max_position = max_pos
        with unittest.mock.patch.object(harness, '_get_market_data') as mock:
            mock.return_value = {'position': {'size': 5000}}
            position = harness.submit_order('LONG', 'AAPL', 100)
            self.assertLessEqual(position['size'], max_pos)


if __name__ == '__main__':
    unittest.main()
```