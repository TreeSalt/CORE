import unittest

from pydantic import ValidationError

from mantis_core.config import EngineConfig, StrategyParams


class TestConfigValidation(unittest.TestCase):
    def test_engine_config_valid(self):
        cfg = EngineConfig(initial_cash=10000)
        self.assertEqual(cfg.initial_cash, 10000)

    def test_engine_config_invalid_cash(self):
        with self.assertRaises(ValidationError):
            EngineConfig(initial_cash=-100)
        with self.assertRaises(ValidationError):
            EngineConfig(initial_cash=0)

    def test_strategy_params_valid(self):
        # Valid: ma_fast < ma_length
        p = StrategyParams(ma_length=100, ma_fast=50)
        self.assertEqual(p.ma_length, 100)

    def test_strategy_params_invalid_ma(self):
        # Invalid: ma_fast >= ma_length
        with self.assertRaises(ValidationError) as cm:
            StrategyParams(ma_length=50, ma_fast=50)
        self.assertIn("ma_fast must be < ma_length", str(cm.exception))

    def test_strategy_params_invalid_stop(self):
        # Invalid: stop_atr <= 0
        with self.assertRaises(ValidationError) as cm:
            StrategyParams(stop_atr=-0.5)
        self.assertIn("stop_atr must be positive", str(cm.exception))

    def test_strategy_params_rsi_inversion(self):
        # Invalid: entry > exit
        with self.assertRaises(ValidationError) as cm:
            StrategyParams(rsi_entry=80, rsi_exit=20)
        self.assertIn("rsi_entry must be < rsi_exit", str(cm.exception))
