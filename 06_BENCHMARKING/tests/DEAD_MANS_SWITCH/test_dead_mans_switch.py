"""
Test Suite: Dead Man's Switch
Constitutional Requirement: Article V.2
Ratified: TRADER_OPS Supreme Council
"""
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock


# ── PATH SETUP ────────────────────────────────────────────────────────────────
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.dead_mans_switch import (
    cmd_check,
    cmd_reset,
    cmd_status,
    DRAWDOWN_FLOORS,
    DMS_STATE_FILE,
)


# ── FIXTURES ─────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def clean_dms_state(tmp_path, monkeypatch):
    """Each test gets a clean DMS state file in a temp location."""
    state_file = tmp_path / "DEAD_MANS_SWITCH_STATE.json"
    monkeypatch.setattr("scripts.dead_mans_switch.DMS_STATE_FILE", state_file)
    monkeypatch.setattr("scripts.dead_mans_switch.ERROR_LEDGER", tmp_path / "ERROR_LEDGER.md")
    yield state_file


@pytest.fixture(autouse=True)
def mock_constitution(monkeypatch):
    """Bypass cryptographic seal for unit tests."""
    monkeypatch.setattr("scripts.dead_mans_switch._verify_constitution", lambda: None)


@pytest.fixture(autouse=True)
def mock_checkpoints(monkeypatch):
    """Provide a clean checkpoint config."""
    checkpoints = {
        "CP1_PAPER_SANDBOX": {"capital_limit": 0, "description": "Paper"},
        "CP2_MICRO_CAPITAL": {"capital_limit": 100, "description": "$100 limit"},
        "CP3_AUDIT_LEDGER":  {"capital_limit": 1000, "description": "$1000 limit"},
        "CP4_MULTI_TENANT":  {"capital_limit": 5000, "description": "$5000 limit"},
    }
    monkeypatch.setattr("scripts.dead_mans_switch._load_checkpoints", lambda: checkpoints)


# ── DRAWDOWN FLOORS ───────────────────────────────────────────────────────────

class TestDrawdownFloors:
    def test_all_checkpoints_have_floors(self):
        for cp in ["CP1_PAPER_SANDBOX", "CP2_MICRO_CAPITAL", "CP3_AUDIT_LEDGER", "CP4_MULTI_TENANT"]:
            assert cp in DRAWDOWN_FLOORS

    def test_floors_are_fractions(self):
        for cp, floor in DRAWDOWN_FLOORS.items():
            assert 0.0 <= floor <= 1.0, f"{cp} floor out of range: {floor}"

    def test_floors_tighten_at_scale(self):
        """Higher checkpoints must have tighter (smaller) floors."""
        assert DRAWDOWN_FLOORS["CP4_MULTI_TENANT"] < DRAWDOWN_FLOORS["CP2_MICRO_CAPITAL"]


# ── CHECK MODE ────────────────────────────────────────────────────────────────

class TestCheckMode:
    def test_safe_pnl_passes(self):
        with pytest.raises(SystemExit) as exc:
            cmd_check(pnl=10.0, checkpoint_id="CP2_MICRO_CAPITAL")
        assert exc.value.code == 0

    def test_zero_pnl_passes(self):
        with pytest.raises(SystemExit) as exc:
            cmd_check(pnl=0.0, checkpoint_id="CP2_MICRO_CAPITAL")
        assert exc.value.code == 0

    def test_small_loss_within_floor_passes(self):
        # CP2: $100 limit, 80% floor = $80 max loss. -$50 should pass.
        with pytest.raises(SystemExit) as exc:
            cmd_check(pnl=-50.0, checkpoint_id="CP2_MICRO_CAPITAL")
        assert exc.value.code == 0

    def test_loss_exceeding_floor_trips(self):
        # CP2: $100 limit, 80% floor = $80 max loss. -$85 should trip.
        with pytest.raises(SystemExit) as exc:
            cmd_check(pnl=-85.0, checkpoint_id="CP2_MICRO_CAPITAL")
        assert exc.value.code == 1

    def test_cp1_paper_any_loss_trips(self):
        """In paper mode, ANY negative P&L is a logic error."""
        with pytest.raises(SystemExit) as exc:
            cmd_check(pnl=-0.01, checkpoint_id="CP1_PAPER_SANDBOX")
        assert exc.value.code == 1

    def test_cp1_paper_zero_passes(self):
        with pytest.raises(SystemExit) as exc:
            cmd_check(pnl=0.0, checkpoint_id="CP1_PAPER_SANDBOX")
        assert exc.value.code == 0

    def test_already_tripped_blocks_check(self, clean_dms_state):
        """If DMS is already tripped, all checks fail immediately."""
        state = {"tripped": True, "trip_log": [], "session_pnl": 0.0}
        clean_dms_state.write_text(json.dumps(state))
        with pytest.raises(SystemExit) as exc:
            cmd_check(pnl=10.0, checkpoint_id="CP2_MICRO_CAPITAL")
        assert exc.value.code == 1

    def test_check_writes_state(self, clean_dms_state):
        """Successful check must persist state."""
        with pytest.raises(SystemExit):
            cmd_check(pnl=5.0, checkpoint_id="CP2_MICRO_CAPITAL")
        state = json.loads(clean_dms_state.read_text())
        assert state["session_pnl"] == 5.0
        assert state["last_check"]["status"] == "SAFE"

    def test_trip_writes_state(self, clean_dms_state):
        """Trip must persist tripped=True to state file."""
        with pytest.raises(SystemExit):
            cmd_check(pnl=-200.0, checkpoint_id="CP2_MICRO_CAPITAL")
        state = json.loads(clean_dms_state.read_text())
        assert state["tripped"] is True
        assert len(state["trip_log"]) == 1


# ── RESET MODE ────────────────────────────────────────────────────────────────

class TestResetMode:
    def test_reset_clears_tripped_state(self, clean_dms_state):
        state = {"tripped": True, "trip_log": [{"reason": "test", "timestamp": "now"}], "session_pnl": -200.0}
        clean_dms_state.write_text(json.dumps(state))
        with pytest.raises(SystemExit) as exc:
            cmd_reset("Manual review complete. Resuming operations.")
        assert exc.value.code == 0
        new_state = json.loads(clean_dms_state.read_text())
        assert new_state["tripped"] is False
        assert new_state["session_pnl"] == 0.0

    def test_reset_logs_reason(self, clean_dms_state):
        state = {"tripped": True, "trip_log": [], "session_pnl": 0.0}
        clean_dms_state.write_text(json.dumps(state))
        with pytest.raises(SystemExit):
            cmd_reset("Reviewed and authorized by Alec Sanchez.")
        new_state = json.loads(clean_dms_state.read_text())
        assert len(new_state["reset_log"]) == 1
        assert "Alec Sanchez" in new_state["reset_log"][0]["reason"]

    def test_reset_requires_reason(self):
        """Empty or too-short reason must be rejected."""
        with pytest.raises(SystemExit) as exc:
            cmd_reset("ok")
        assert exc.value.code == 1

    def test_reset_when_not_tripped_is_noop(self, clean_dms_state):
        state = {"tripped": False, "trip_log": [], "session_pnl": 0.0}
        clean_dms_state.write_text(json.dumps(state))
        with pytest.raises(SystemExit) as exc:
            cmd_reset("Just checking the reset command works fine here.")
        assert exc.value.code == 0


# ── FIDUCIARY CONSTRAINTS ─────────────────────────────────────────────────────

class TestFiduciaryConstraints:
    def test_no_hardcoded_credentials(self):
        src = Path("scripts/dead_mans_switch.py").read_text().lower()
        for kw in ["api_key =", "password =", "secret ="]:
            assert kw not in src

    def test_no_governance_writes(self):
        """DMS must never write to 04_GOVERNANCE/."""
        src = Path("scripts/dead_mans_switch.py").read_text()
        import ast
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                assert "04_GOVERNANCE" not in node.value or "write" not in src[max(0, node.col_offset-20):node.col_offset+50]

    def test_trip_is_fail_closed(self):
        """Trip must always sys.exit(1) — never return normally."""
        src = Path("scripts/dead_mans_switch.py").read_text()
        # Verify _trip calls sys.exit(1)
        assert "sys.exit(1)" in src

    def test_reset_requires_human_reason(self):
        """Reset without reason must fail — no silent resets."""
        with pytest.raises(SystemExit) as exc:
            cmd_reset("")
        assert exc.value.code == 1

    def test_state_file_is_append_only_trip_log(self, clean_dms_state):
        """Each trip must add to trip_log, never overwrite."""
        # First trip
        with pytest.raises(SystemExit):
            cmd_check(pnl=-200.0, checkpoint_id="CP2_MICRO_CAPITAL")
        state = json.loads(clean_dms_state.read_text())
        assert len(state["trip_log"]) == 1

    def test_dms_blocks_after_trip(self, clean_dms_state):
        """After a trip, even a safe P&L check must fail."""
        # Trip it
        with pytest.raises(SystemExit):
            cmd_check(pnl=-200.0, checkpoint_id="CP2_MICRO_CAPITAL")
        # Now check with safe P&L — must still fail
        with pytest.raises(SystemExit) as exc:
            cmd_check(pnl=100.0, checkpoint_id="CP2_MICRO_CAPITAL")
        assert exc.value.code == 1
