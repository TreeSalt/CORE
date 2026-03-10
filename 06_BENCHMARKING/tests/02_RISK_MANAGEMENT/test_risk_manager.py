"""
Benchmark Test Suite: 02_RISK_MANAGEMENT
Domain: RiskManager class
Ratified: 2026-03-09
"""
import pytest
from risk_management.risk_manager import RiskManager, RiskViolationError


def test_required_imports_exist():
    from risk_management.risk_manager import RiskManager, RiskViolationError
    assert RiskManager is not None
    assert RiskViolationError is not None


class TestRiskManagerInit:
    def test_initializes_with_limits(self):
        rm = RiskManager(max_trade_loss=500, max_daily_loss=2000)
        assert rm.max_trade_loss == 500
        assert rm.max_daily_loss == 2000

    def test_daily_loss_starts_at_zero(self):
        rm = RiskManager(max_trade_loss=500, max_daily_loss=2000)
        assert rm.get_daily_loss() == 0.0

    def test_ledger_starts_empty(self):
        rm = RiskManager(max_trade_loss=500, max_daily_loss=2000)
        assert rm.get_position_ledger() == {}


class TestTradeApproval:
    def setup_method(self):
        self.rm = RiskManager(max_trade_loss=500, max_daily_loss=2000)

    def test_approves_trade_within_limits(self):
        result = self.rm.approve_trade("MES", quantity=1, estimated_loss=100)
        assert result is True

    def test_rejects_trade_exceeding_per_trade_limit(self):
        with pytest.raises(RiskViolationError):
            self.rm.approve_trade("MES", quantity=1, estimated_loss=600)

    def test_rejects_trade_that_would_breach_daily_limit(self):
        self.rm.record_loss(1800)
        with pytest.raises(RiskViolationError):
            self.rm.approve_trade("MES", quantity=1, estimated_loss=300)

    def test_reads_ledger_before_approving(self):
        self.rm.update_position_ledger("MES", 5)
        result = self.rm.approve_trade("MES", quantity=1, estimated_loss=100)
        assert result is True


class TestLossTracking:
    def setup_method(self):
        self.rm = RiskManager(max_trade_loss=500, max_daily_loss=2000)

    def test_record_loss_accumulates(self):
        self.rm.record_loss(300)
        self.rm.record_loss(400)
        assert self.rm.get_daily_loss() == 700.0

    def test_daily_loss_at_limit_blocks_trade(self):
        self.rm.record_loss(2000)
        with pytest.raises(RiskViolationError):
            self.rm.approve_trade("MES", quantity=1, estimated_loss=1)

    def test_reset_daily_loss(self):
        self.rm.record_loss(1000)
        self.rm.reset_daily_loss()
        assert self.rm.get_daily_loss() == 0.0


class TestPositionLedger:
    def setup_method(self):
        self.rm = RiskManager(max_trade_loss=500, max_daily_loss=2000)

    def test_update_ledger_tracks_position(self):
        self.rm.update_position_ledger("MES", 3)
        assert self.rm.get_position_ledger()["MES"] == 3

    def test_update_ledger_accumulates(self):
        self.rm.update_position_ledger("MES", 3)
        self.rm.update_position_ledger("MES", 2)
        assert self.rm.get_position_ledger()["MES"] == 5

    def test_ledger_tracks_multiple_instruments(self):
        self.rm.update_position_ledger("MES", 3)
        self.rm.update_position_ledger("SPY", 10)
        ledger = self.rm.get_position_ledger()
        assert ledger["MES"] == 3
        assert ledger["SPY"] == 10


class TestFiduciaryConstraints:
    def test_risk_violation_error_is_exception(self):
        assert issubclass(RiskViolationError, Exception)

    def test_no_governance_domain_imports(self):
        import ast, pathlib
        src = pathlib.Path("02_RISK_MANAGEMENT/risk_management/risk_manager.py").read_text()
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                mod = getattr(node, 'module', '') or ''
                assert '04_GOVERNANCE' not in mod

    def test_no_hardcoded_credentials(self):
        import pathlib
        src = pathlib.Path("02_RISK_MANAGEMENT/risk_management/risk_manager.py").read_text().lower()
        for keyword in ['password', 'api_key', 'secret', 'token']:
            assert f'{keyword} =' not in src

    def test_loss_breach_is_logged(self):
        import logging
        from unittest.mock import patch
        rm = RiskManager(max_trade_loss=500, max_daily_loss=2000)
        with patch('logging.warning') as mock_log:
            try:
                rm.approve_trade("MES", quantity=1, estimated_loss=600)
            except RiskViolationError:
                pass
            mock_log.assert_called()
