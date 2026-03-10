"""
Benchmark Test Suite: 00_PHYSICS_ENGINE
Domain: PhysicsEngine class
Ratified: 2026-03-09
"""
import pytest
from physics_engine.physics_engine import PhysicsEngine, PhysicsViolationError


# ── IMPORTS ──────────────────────────────────────────────────────────────────

def test_required_imports_exist():
    from physics_engine.physics_engine import PhysicsEngine, PhysicsViolationError
    assert PhysicsEngine is not None
    assert PhysicsViolationError is not None


# ── INITIALIZATION ────────────────────────────────────────────────────────────

class TestPhysicsEngineInit:
    def test_initializes_with_position_limits(self):
        limits = {"MES": 10, "SPY": 50}
        engine = PhysicsEngine(limits)
        assert engine.position_limits == limits

    def test_ledger_starts_empty(self):
        engine = PhysicsEngine({"MES": 10})
        assert engine.get_open_positions() == {}


# ── P&L CALCULATION ───────────────────────────────────────────────────────────

class TestPnLCalculation:
    def setup_method(self):
        self.engine = PhysicsEngine({"MES": 100})
        self.engine.track_open_position("MES", 5)

    def test_positive_pl_on_price_increase(self):
        pl = self.engine.calculate_position_pl("MES", 5010, 5000)
        assert pl == 50.0  # 5 contracts * 10 ticks

    def test_negative_pl_on_price_decrease(self):
        pl = self.engine.calculate_position_pl("MES", 4990, 5000)
        assert pl == -50.0

    def test_zero_pl_on_unchanged_price(self):
        pl = self.engine.calculate_position_pl("MES", 5000, 5000)
        assert pl == 0.0

    def test_pl_zero_for_unknown_instrument(self):
        pl = self.engine.calculate_position_pl("UNKNOWN", 100, 90)
        assert pl == 0.0


# ── POSITION TRACKING ─────────────────────────────────────────────────────────

class TestPositionTracking:
    def setup_method(self):
        self.engine = PhysicsEngine({"MES": 100, "SPY": 200})

    def test_track_new_position(self):
        self.engine.track_open_position("MES", 10)
        assert self.engine.get_open_positions()["MES"] == 10

    def test_track_accumulates_positions(self):
        self.engine.track_open_position("MES", 10)
        self.engine.track_open_position("MES", 5)
        assert self.engine.get_open_positions()["MES"] == 15

    def test_track_multiple_instruments(self):
        self.engine.track_open_position("MES", 10)
        self.engine.track_open_position("SPY", 20)
        positions = self.engine.get_open_positions()
        assert positions["MES"] == 10
        assert positions["SPY"] == 20


# ── POSITION LIMIT ENFORCEMENT ────────────────────────────────────────────────

class TestPositionLimits:
    def setup_method(self):
        self.engine = PhysicsEngine({"MES": 10})

    def test_raises_on_limit_breach(self):
        with pytest.raises(PhysicsViolationError):
            self.engine.track_open_position("MES", 11)

    def test_exactly_at_limit_does_not_raise(self):
        self.engine.track_open_position("MES", 10)  # should not raise

    def test_accumulation_breach_raises(self):
        self.engine.track_open_position("MES", 8)
        with pytest.raises(PhysicsViolationError):
            self.engine.track_open_position("MES", 5)


# ── CLOSE POSITION ────────────────────────────────────────────────────────────

class TestClosePosition:
    def setup_method(self):
        self.engine = PhysicsEngine({"MES": 100})
        self.engine.track_open_position("MES", 10)

    def test_close_reduces_position(self):
        self.engine.close_position("MES", 4)
        assert self.engine.get_open_positions()["MES"] == 6

    def test_close_nonexistent_raises(self):
        with pytest.raises((ValueError, PhysicsViolationError)):
            self.engine.close_position("SPY", 1)

    def test_close_more_than_open_raises(self):
        with pytest.raises((ValueError, PhysicsViolationError)):
            self.engine.close_position("MES", 99)


# ── FIDUCIARY CONSTRAINTS ─────────────────────────────────────────────────────

class TestFiduciaryConstraints:
    def test_no_governance_domain_imports(self):
        import ast, pathlib
        src = pathlib.Path("00_PHYSICS_ENGINE/physics_engine/physics_engine.py").read_text()
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                mod = getattr(node, 'module', '') or ''
                assert '04_GOVERNANCE' not in mod

    def test_no_hardcoded_credentials(self):
        import pathlib
        src = pathlib.Path("00_PHYSICS_ENGINE/physics_engine/physics_engine.py").read_text().lower()
        for keyword in ['password', 'api_key', 'secret', 'token']:
            assert f'{keyword} =' not in src

    def test_physics_violation_error_is_exception(self):
        assert issubclass(PhysicsViolationError, Exception)
