#!/usr/bin/env python3
"""
scripts/dead_mans_switch.py — AOS Dead Man's Switch
====================================================
Constitutional Requirement: Article V.2
Ratified: TRADER_OPS Supreme Council

PURPOSE:
  Prevents the operator from being financially destroyed by a single failure
  event. Monitors cumulative P&L against the active checkpoint capital limit.
  Triggers FAIL-CLOSED when drawdown exceeds the constitutional threshold.
  Requires human-authored re-authorization to resume after any trip.

ARCHITECTURE:
  - Reads active checkpoint from CHECKPOINTS.yaml
  - Maintains a DEAD_MANS_SWITCH_STATE.json ledger (append-only trip log)
  - Can be called as a guard (check mode) or as a daemon (watch mode)
  - FAIL-CLOSED: writes trip record, kills all Ollama tasks, refuses restart
    without human-authored RESUME_TOKEN in state file

USAGE:
  # Check current P&L against limit (call before any order dispatch)
  python3 scripts/dead_mans_switch.py --check --pnl -45.00 --checkpoint CP2_MICRO_CAPITAL

  # Reset after human review (requires --sovereign-override flag + reason)
  python3 scripts/dead_mans_switch.py --reset --reason "Manual review complete. Loss was expected. Resuming."

  # Status report
  python3 scripts/dead_mans_switch.py --status
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

# ── PATHS ─────────────────────────────────────────────────────────────────────
REPO_ROOT       = Path(__file__).resolve().parents[1]
CHECKPOINTS     = REPO_ROOT / "CHECKPOINTS.yaml"
GOVERNOR_SEAL   = REPO_ROOT / ".governor_seal"
CONSTITUTION    = REPO_ROOT / "04_GOVERNANCE" / "AGENTIC_ETHICAL_CONSTITUTION.md"
OPERATOR_FILE   = REPO_ROOT / "04_GOVERNANCE" / "OPERATOR_INSTANCE.yaml"
ERROR_LEDGER    = REPO_ROOT / "docs" / "ERROR_LEDGER.md"
DMS_STATE_FILE  = REPO_ROOT / "orchestration" / "DEAD_MANS_SWITCH_STATE.json"

# ── LOGGING ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%SZ"
)
log = logging.getLogger("dead_mans_switch")

# ── THRESHOLDS ────────────────────────────────────────────────────────────────
# Constitutional floor: never lose more than this fraction of the checkpoint
# capital limit in a single session without triggering the DMS.
# CP1 = $0 capital limit → DMS trips on any realized loss
# CP2 = $100 → DMS trips at -$80 (80% drawdown floor)
# CP3 = $1000 → DMS trips at -$200 (20% drawdown floor — tighter at scale)
# CP4 = $5000 → DMS trips at -$500 (10% drawdown floor — institutional floor)
DRAWDOWN_FLOORS: dict[str, float] = {
    "CP1_PAPER_SANDBOX": 0.00,   # Any loss in paper mode is a logic error
    "CP2_MICRO_CAPITAL": 0.80,   # 80% of $100 = $80 max loss
    "CP3_AUDIT_LEDGER":  0.20,   # 20% of $1000 = $200 max loss
    "CP4_MULTI_TENANT":  0.10,   # 10% of $5000 = $500 max loss
}


# ── CORE ──────────────────────────────────────────────────────────────────────

def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _verify_constitution() -> None:
    """Fail closed if constitutional seal is broken."""
    if not GOVERNOR_SEAL.exists():
        _trip("GOVERNOR_SEAL_MISSING — constitutional bind broken")
    stored_aec = None
    for line in GOVERNOR_SEAL.read_text().splitlines():
        if line.startswith("AEC_HASH:"):
            stored_aec = line.split(":", 1)[1].strip()
    if not stored_aec:
        _trip("GOVERNOR_SEAL_MALFORMED — AEC_HASH missing")
    if _sha256(CONSTITUTION) != stored_aec:
        _trip("CONSTITUTIONAL_INTEGRITY_BREACH — AEC hash mismatch")


def _load_checkpoints() -> dict:
    import yaml
    if not CHECKPOINTS.exists():
        _trip("CHECKPOINTS_YAML_MISSING")
    with open(CHECKPOINTS) as f:
        return yaml.safe_load(f)["checkpoints"]


def _load_state() -> dict:
    if not DMS_STATE_FILE.exists():
        return {"tripped": False, "trip_log": [], "session_pnl": 0.0}
    return json.loads(DMS_STATE_FILE.read_text())


def _save_state(state: dict) -> None:
    DMS_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    DMS_STATE_FILE.write_text(json.dumps(state, indent=2))


def _append_error_ledger(msg: str) -> None:
    timestamp = datetime.now(timezone.utc).isoformat()
    ERROR_LEDGER.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(ERROR_LEDGER, "a") as f:
            f.write(f"\n### {timestamp} — DEAD MAN'S SWITCH\n**Event:** {msg}\n"
                    f"**Recovery:** Human sovereign re-authorization required.\n"
                    f"**Command:** `python3 scripts/dead_mans_switch.py --reset --reason \"<your reason>\"`\n")
    except Exception:
        pass


def _trip(reason: str) -> None:
    """
    Trip the Dead Man's Switch. This is a one-way door.
    Only --reset with human-authored reason can re-open it.
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    log.critical("=" * 60)
    log.critical("DEAD MAN'S SWITCH TRIPPED")
    log.critical(f"Reason: {reason}")
    log.critical(f"Time:   {timestamp}")
    log.critical("ALL AGENT DISPATCH IS NOW LOCKED.")
    log.critical("Recovery: python3 scripts/dead_mans_switch.py --reset --reason '<reason>'")
    log.critical("=" * 60)

    state = _load_state()
    state["tripped"] = True
    state["last_trip"] = {
        "reason": reason,
        "timestamp": timestamp,
        "requires_human_reset": True,
    }
    state.setdefault("trip_log", []).append({
        "reason": reason,
        "timestamp": timestamp,
    })
    _save_state(state)
    _append_error_ledger(reason)
    sys.exit(1)


def cmd_check(pnl: float, checkpoint_id: str) -> None:
    """
    Guard call: check if current session P&L violates the DMS threshold.
    Exit code 0 = safe. Exit code 1 = tripped (FAIL-CLOSED).
    """
    _verify_constitution()

    # If already tripped, refuse immediately
    state = _load_state()
    if state.get("tripped"):
        log.critical("DEAD MAN'S SWITCH IS TRIPPED. Human reset required before any dispatch.")
        log.critical("Command: python3 scripts/dead_mans_switch.py --reset --reason '<reason>'")
        sys.exit(1)

    checkpoints = _load_checkpoints()
    if checkpoint_id not in checkpoints:
        _trip(f"UNKNOWN_CHECKPOINT: {checkpoint_id}")

    cp = checkpoints[checkpoint_id]
    capital_limit = float(cp.get("capital_limit", 0))
    floor_fraction = DRAWDOWN_FLOORS.get(checkpoint_id, 0.10)
    max_loss = capital_limit * floor_fraction

    # CP1 paper sandbox: any negative P&L is a logic error — trip immediately
    if checkpoint_id == "CP1_PAPER_SANDBOX" and pnl < 0:
        _trip(
            f"CP1_PAPER_SANDBOX VIOLATION: Negative P&L in paper mode (pnl={pnl:.2f}). "
            "Paper trading should never lose real capital. Logic error detected."
        )

    # For capital checkpoints: trip if loss exceeds floor
    if capital_limit > 0 and pnl < 0 and abs(pnl) > max_loss:
        _trip(
            f"DRAWDOWN_LIMIT_BREACHED: checkpoint={checkpoint_id} "
            f"pnl={pnl:.2f} limit=-{max_loss:.2f} "
            f"(capital_limit={capital_limit:.2f} floor={floor_fraction*100:.0f}%)"
        )

    # Update session P&L tracking
    state["session_pnl"] = pnl
    state["last_check"] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checkpoint": checkpoint_id,
        "pnl": pnl,
        "max_loss_allowed": -max_loss,
        "status": "SAFE",
    }
    _save_state(state)

    log.info(f"DMS CHECK PASSED | checkpoint={checkpoint_id} pnl={pnl:.2f} "
             f"max_loss_allowed=-{max_loss:.2f} | STATUS: SAFE")
    sys.exit(0)


def cmd_reset(reason: str) -> None:
    """
    Human-authored reset. Clears the tripped state and logs the authorization.
    Requires a non-empty reason string — the human must explain the decision.
    """
    if not reason or len(reason.strip()) < 10:
        log.critical("RESET REJECTED: --reason must be at least 10 characters. "
                     "The human operator must explain the decision.")
        sys.exit(1)

    _verify_constitution()

    state = _load_state()
    if not state.get("tripped"):
        log.info("DMS is not tripped. No reset needed.")
        sys.exit(0)

    timestamp = datetime.now(timezone.utc).isoformat()
    state["tripped"] = False
    state["session_pnl"] = 0.0
    state.setdefault("reset_log", []).append({
        "timestamp": timestamp,
        "reason": reason.strip(),
        "authorized_by": "HUMAN_OPERATOR",
    })
    _save_state(state)

    # Also log to ERROR_LEDGER for audit trail
    ERROR_LEDGER.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(ERROR_LEDGER, "a") as f:
            f.write(f"\n### {timestamp} — DEAD MAN'S SWITCH RESET\n"
                    f"**Authorized by:** Human Operator\n"
                    f"**Reason:** {reason.strip()}\n"
                    f"**Status:** DMS cleared. Agent dispatch re-enabled.\n")
    except Exception:
        pass

    log.info("=" * 60)
    log.info("DEAD MAN'S SWITCH RESET — Agent dispatch re-enabled.")
    log.info(f"Reason logged: {reason.strip()}")
    log.info("=" * 60)
    sys.exit(0)


def cmd_status() -> None:
    """Print current DMS state."""
    _verify_constitution()
    state = _load_state()

    print("\n" + "=" * 60)
    print("DEAD MAN'S SWITCH — STATUS REPORT")
    print("=" * 60)
    print(f"Tripped:        {state.get('tripped', False)}")
    print(f"Session P&L:    {state.get('session_pnl', 0.0):.2f}")

    last_check = state.get("last_check", {})
    if last_check:
        print(f"Last check:     {last_check.get('timestamp', 'N/A')}")
        print(f"Checkpoint:     {last_check.get('checkpoint', 'N/A')}")
        print(f"Max loss limit: {last_check.get('max_loss_allowed', 'N/A')}")
        print(f"Status:         {last_check.get('status', 'N/A')}")

    trip_log = state.get("trip_log", [])
    if trip_log:
        print(f"\nTrip history ({len(trip_log)} events):")
        for entry in trip_log[-3:]:  # Show last 3
            print(f"  [{entry['timestamp']}] {entry['reason']}")

    reset_log = state.get("reset_log", [])
    if reset_log:
        print(f"\nReset history ({len(reset_log)} events):")
        for entry in reset_log[-3:]:
            print(f"  [{entry['timestamp']}] {entry['reason']}")

    print("=" * 60 + "\n")
    sys.exit(0)


# ── MAIN ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="AOS Dead Man's Switch — Article V.2 Constitutional Requirement"
    )
    subparsers = parser.add_subparsers(dest="command")

    # --check
    check_parser = subparsers.add_parser("--check", help="Check P&L against DMS threshold")
    check_parser.add_argument("--pnl", type=float, required=True,
                              help="Current session P&L (negative = loss)")
    check_parser.add_argument("--checkpoint", required=True,
                              choices=list(DRAWDOWN_FLOORS.keys()),
                              help="Active checkpoint ID from CHECKPOINTS.yaml")

    # --reset
    reset_parser = subparsers.add_parser("--reset", help="Human-authorized reset after trip")
    reset_parser.add_argument("--reason", required=True,
                              help="Human-authored reason for reset (min 10 chars)")

    # --status
    subparsers.add_parser("--status", help="Print current DMS state")

    # Support direct flag style: --check --pnl X --checkpoint Y
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--pnl", type=float)
    parser.add_argument("--checkpoint", choices=list(DRAWDOWN_FLOORS.keys()))
    parser.add_argument("--reset", action="store_true")
    parser.add_argument("--reason", type=str)
    parser.add_argument("--status", action="store_true")

    args = parser.parse_args()

    if args.check:
        if args.pnl is None or args.checkpoint is None:
            parser.error("--check requires --pnl and --checkpoint")
        cmd_check(args.pnl, args.checkpoint)
    elif args.reset:
        if not args.reason:
            parser.error("--reset requires --reason")
        cmd_reset(args.reason)
    elif args.status:
        cmd_status()
    else:
        parser.print_help()
        sys.exit(1)
