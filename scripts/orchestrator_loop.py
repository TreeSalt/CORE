#!/usr/bin/env python3
"""
scripts/orchestrator_loop.py — AOS Phase 2 Auto-Delegator
==========================================================
Constitutional Requirement: Phase 2 — Remove human as messenger
Ratified: TRADER_OPS Supreme Council — 2026-03-10

PURPOSE:
  Closes the last human-in-the-loop gap: the sovereign no longer needs to
  manually relay missions from Claude (Supreme Council) to the factory agents.

  Claude writes missions to MISSION_QUEUE.json.
  This loop picks them up, fires run_loop.py, handles results, and
  escalates to the sovereign ONLY when genuinely required.

SOVEREIGN IS ONLY PAGED WHEN:
  1. IMPLEMENTATION proposal passes — requires ratification signature
  2. HARD FAIL — constitutional violation, sovereign diagnosis required
  3. MAX RETRIES exhausted — sovereign decides next action
  4. make drop fails — sovereign reviews gate report

EVERYTHING ELSE IS AUTONOMOUS:
  - ARCHITECTURE proposals: auto-ratified (blueprints don't touch capital)
  - Soft fails: run_loop.py handles retries internally
  - Queue management: fully automatic
  - Drop packet: triggered automatically after each ratification batch

MISSION QUEUE FORMAT (orchestration/MISSION_QUEUE.json):
  {
    "missions": [
      {
        "id": "unique_mission_id",
        "domain": "01_DATA_INGESTION",
        "task": "implement_something",
        "mission_file": "mission_something.md",
        "type": "IMPLEMENTATION",
        "max_retries": 3,
        "status": "PENDING",
        "priority": 1,
        "authored_by": "Claude.ai",
        "authored_at": "2026-03-10T00:00:00Z",
        "result": null
      }
    ]
  }

USAGE:
  # Run once — processes all PENDING missions in priority order
  python3 scripts/orchestrator_loop.py

  # Run as daemon — polls queue every N seconds
  python3 scripts/orchestrator_loop.py --daemon --interval 60

  # Dry run — show what would execute without running anything
  python3 scripts/orchestrator_loop.py --dry-run
"""

from __future__ import annotations

import argparse
import json
import logging
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# ── PATHS ─────────────────────────────────────────────────────────────────────
REPO_ROOT       = Path(__file__).resolve().parents[1]
MISSION_QUEUE   = REPO_ROOT / "orchestration" / "MISSION_QUEUE.json"
MISSIONS_DIR    = REPO_ROOT / "prompts" / "missions"
ESCALATION_DIR  = REPO_ROOT / "08_IMPLEMENTATION_NOTES" / "ESCALATIONS"
ERROR_LEDGER    = REPO_ROOT / "docs" / "ERROR_LEDGER.md"
RUN_LOOP        = REPO_ROOT / "scripts" / "run_loop.py"
ORCH_STATE      = REPO_ROOT / "orchestration" / "ORCHESTRATOR_STATE.json"

# ── LOGGING ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%SZ"
)
log = logging.getLogger("orchestrator_loop")


# ── QUEUE MANAGEMENT ──────────────────────────────────────────────────────────

def load_queue() -> dict:
    if not MISSION_QUEUE.exists():
        return {"missions": []}
    return json.loads(MISSION_QUEUE.read_text())

def save_queue(queue: dict) -> None:
    MISSION_QUEUE.parent.mkdir(parents=True, exist_ok=True)
    MISSION_QUEUE.write_text(json.dumps(queue, indent=2))

def get_pending(queue: dict) -> list[dict]:
    return sorted(
        [m for m in queue["missions"] if m["status"] == "PENDING"],
        key=lambda m: m.get("priority", 99)
    )

def update_mission(queue: dict, mission_id: str, updates: dict) -> None:
    for m in queue["missions"]:
        if m["id"] == mission_id:
            m.update(updates)
            return

def load_state() -> dict:
    if not ORCH_STATE.exists():
        return {"runs": [], "last_drop_version": None}
    return json.loads(ORCH_STATE.read_text())

def save_state(state: dict) -> None:
    ORCH_STATE.parent.mkdir(parents=True, exist_ok=True)
    ORCH_STATE.write_text(json.dumps(state, indent=2))

def append_error_ledger(msg: str) -> None:
    timestamp = datetime.now(timezone.utc).isoformat()
    ERROR_LEDGER.parent.mkdir(parents=True, exist_ok=True)
    with open(ERROR_LEDGER, "a") as f:
        f.write(f"\n### {timestamp} — ORCHESTRATOR\n{msg}\n")


# ── RATIFICATION ──────────────────────────────────────────────────────────────

def auto_ratify(proposal_path: str, mission: dict) -> bool:
    """
    ARCHITECTURE proposals are auto-ratified — they produce blueprints,
    not executable code, and cannot touch capital.
    IMPLEMENTATION proposals always require sovereign signature.
    """
    if mission.get("type") == "ARCHITECTURE":
        path = Path(proposal_path)
        if path.exists():
            content = path.read_text()
            content = content.replace("STATUS: PENDING_REVIEW", "STATUS: RATIFIED")
            path.write_text(content)
            log.info(f"AUTO-RATIFIED (ARCHITECTURE): {path.name}")
            return True
    return False

def write_sovereign_escalation(mission: dict, ratification_packet: str) -> str:
    """Write a human-readable sovereign action required notice."""
    ESCALATION_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = ESCALATION_DIR / f"SOVEREIGN_ACTION_{mission['domain']}_{ts}.md"

    lines = [
        "# SOVEREIGN ACTION REQUIRED",
        f"**Mission ID:** {mission['id']}",
        f"**Domain:** {mission['domain']}",
        f"**Task:** {mission['task']}",
        f"**Type:** {mission['type']}",
        f"**Timestamp:** {ts}",
        "",
        "## Action Required",
        "The factory has produced a passing IMPLEMENTATION proposal.",
        "Sovereign review and ratification is required before this code",
        "is considered production-ready.",
        "",
        "## Ratification Packet",
        f"`{ratification_packet}`",
        "",
        "## Steps",
        "1. Review the proposal linked in the ratification packet above",
        "2. If satisfied: change STATUS: PENDING_REVIEW → STATUS: RATIFIED",
        "3. Run: `make drop` to seal the new version",
        "4. The orchestrator will automatically continue the queue",
        "",
        "**The factory is paused on this domain until ratification is complete.**",
    ]
    path.write_text("\n".join(lines))

    log.critical("=" * 60)
    log.critical("SOVEREIGN RATIFICATION REQUIRED")
    log.critical(f"Domain: {mission['domain']} | Task: {mission['task']}")
    log.critical(f"Packet: {ratification_packet}")
    log.critical(f"Notice: {path}")
    log.critical("=" * 60)
    return str(path)


# ── DROP PACKET ───────────────────────────────────────────────────────────────

def trigger_drop(non_blocking: bool = True) -> bool:
    """
    Trigger make drop. Non-blocking by default — factory keeps running.
    The sovereign reviews the drop packet asynchronously.
    """
    log.info("Triggering make drop...")
    try:
        if non_blocking:
            # Fire and forget — don't block the queue
            subprocess.Popen(
                ["make", "drop"],
                cwd=str(REPO_ROOT),
                stdout=open(REPO_ROOT / "orchestration" / "last_drop.log", "w"),
                stderr=subprocess.STDOUT
            )
            log.info("make drop fired (non-blocking) — see orchestration/last_drop.log")
            return True
        else:
            result = subprocess.run(
                ["make", "drop"],
                cwd=str(REPO_ROOT),
                capture_output=True, text=True, timeout=300
            )
            if result.returncode == 0:
                log.info("make drop complete ✅")
                return True
            else:
                log.error(f"make drop failed:\n{result.stdout[-2000:]}")
                return False
    except Exception as e:
        log.error(f"make drop exception: {e}")
        return False


# ── MISSION EXECUTION ─────────────────────────────────────────────────────────

def execute_mission(mission: dict, dry_run: bool = False) -> dict:
    """
    Fire run_loop.py for a single mission. Returns result dict.
    """
    mission_file = mission["mission_file"]
    mission_path = MISSIONS_DIR / mission_file

    if not mission_path.exists():
        return {
            "status": "HARD_FAIL",
            "reason": f"Mission file not found: {mission_path}",
            "ratification_packet": None,
        }

    cmd = [
        sys.executable, str(RUN_LOOP),
        "--domain",      mission["domain"],
        "--task",        mission["task"],
        "--mission",     mission_file,
        "--type",        mission.get("type", "IMPLEMENTATION"),
        "--max-retries", str(mission.get("max_retries", 3)),
    ]

    log.info(f"Executing mission: {mission['id']}")
    log.info(f"  Domain:  {mission['domain']}")
    log.info(f"  Task:    {mission['task']}")
    log.info(f"  Type:    {mission.get('type', 'IMPLEMENTATION')}")

    if dry_run:
        log.info(f"  DRY RUN — would execute: {' '.join(cmd)}")
        return {"status": "DRY_RUN", "reason": "dry_run=True", "ratification_packet": None}

    try:
        result = subprocess.run(
            cmd, cwd=str(REPO_ROOT),
            capture_output=False,  # let output stream live
            timeout=2400           # 40min hard ceiling per mission
        )

        if result.returncode == 0:
            # Find the most recent ratification packet for this domain
            packets = sorted(
                ESCALATION_DIR.glob(f"RATIFICATION_{mission['domain']}_*.md"),
                key=lambda p: p.stat().st_mtime, reverse=True
            )
            packet = str(packets[0]) if packets else None
            return {"status": "PASS", "ratification_packet": packet}

        else:
            # Find escalation packet
            packets = sorted(
                ESCALATION_DIR.glob(f"ESCALATION_{mission['domain']}_*.md"),
                key=lambda p: p.stat().st_mtime, reverse=True
            )
            packet = str(packets[0]) if packets else None
            return {
                "status": "ESCALATE",
                "reason": "run_loop exhausted or hard failed",
                "escalation_packet": packet,
                "ratification_packet": None,
            }

    except subprocess.TimeoutExpired:
        return {
            "status": "HARD_FAIL",
            "reason": "Mission timed out after 40 minutes",
            "ratification_packet": None,
        }
    except Exception as e:
        return {
            "status": "HARD_FAIL",
            "reason": str(e),
            "ratification_packet": None,
        }


# ── MAIN LOOP ─────────────────────────────────────────────────────────────────

def run_orchestrator(dry_run: bool = False,
                     daemon: bool = False,
                     interval: int = 60) -> None:

    log.info("=" * 60)
    log.info("AOS ORCHESTRATOR LOOP — PHASE 2 AUTO-DELEGATOR")
    log.info(f"Mode: {'DAEMON' if daemon else 'SINGLE-PASS'} | dry_run={dry_run}")
    log.info("=" * 60)

    ratifications_pending = []

    while True:
        queue = load_queue()
        state = load_state()
        pending = get_pending(queue)

        if not pending:
            if daemon:
                log.info(f"Queue empty — sleeping {interval}s...")
                time.sleep(interval)
                continue
            else:
                log.info("Queue empty — orchestrator complete.")
                break

        log.info(f"Queue: {len(pending)} mission(s) pending")

        for mission in pending:
            log.info(f"\n{'─'*50}")
            log.info(f"MISSION: {mission['id']}")

            # Mark in-progress
            update_mission(queue, mission["id"], {
                "status": "IN_PROGRESS",
                "started_at": datetime.now(timezone.utc).isoformat()
            })
            save_queue(queue)

            # Execute
            result = execute_mission(mission, dry_run=dry_run)

            # Handle result
            if result["status"] == "PASS":
                packet = result.get("ratification_packet")

                # ARCHITECTURE: auto-ratify, no sovereign needed
                if auto_ratify(packet, mission) if packet else False:
                    update_mission(queue, mission["id"], {
                        "status": "RATIFIED",
                        "completed_at": datetime.now(timezone.utc).isoformat(),
                        "result": result,
                    })
                    log.info(f"✅ COMPLETE (auto-ratified): {mission['id']}")

                else:
                    # IMPLEMENTATION: page sovereign
                    notice = write_sovereign_escalation(mission, packet or "NOT FOUND")
                    update_mission(queue, mission["id"], {
                        "status": "AWAITING_RATIFICATION",
                        "completed_at": datetime.now(timezone.utc).isoformat(),
                        "result": result,
                        "sovereign_notice": notice,
                    })
                    ratifications_pending.append(mission["id"])
                    append_error_ledger(
                        f"AWAITING_RATIFICATION: {mission['domain']} "
                        f"task={mission['task']} packet={packet}"
                    )

            elif result["status"] in ("HARD_FAIL", "ESCALATE"):
                update_mission(queue, mission["id"], {
                    "status": result["status"],
                    "completed_at": datetime.now(timezone.utc).isoformat(),
                    "result": result,
                })
                append_error_ledger(
                    f"ORCHESTRATOR {result['status']}: {mission['domain']} "
                    f"reason={result.get('reason', 'see escalation packet')}"
                )
                log.critical(f"❌ {result['status']}: {mission['id']} — sovereign review required")

            elif result["status"] == "DRY_RUN":
                update_mission(queue, mission["id"], {"status": "PENDING"})

            save_queue(queue)

        # After processing batch — trigger drop non-blocking
        if not dry_run and ratifications_pending:
            log.info(f"\n{len(ratifications_pending)} mission(s) awaiting ratification.")
            log.info("Triggering make drop (non-blocking)...")
            trigger_drop(non_blocking=True)

        state["runs"].append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "processed": len(pending),
            "ratifications_pending": ratifications_pending,
        })
        save_state(state)

        if not daemon:
            break
        time.sleep(interval)

    # Final summary
    queue = load_queue()
    awaiting = [m for m in queue["missions"] if m["status"] == "AWAITING_RATIFICATION"]
    failed   = [m for m in queue["missions"] if m["status"] in ("HARD_FAIL", "ESCALATE")]

    log.info("\n" + "=" * 60)
    log.info("ORCHESTRATOR RUN COMPLETE")
    log.info(f"Awaiting sovereign ratification: {len(awaiting)}")
    log.info(f"Failed/escalated: {len(failed)}")
    if awaiting:
        log.info("Ratification required for:")
        for m in awaiting:
            log.info(f"  - {m['domain']} / {m['task']}")
    log.info("=" * 60)


# ── ENTRY POINT ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="AOS Orchestrator Loop — Phase 2 Auto-Delegator"
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would execute without running anything")
    parser.add_argument("--daemon", action="store_true",
                        help="Poll queue continuously")
    parser.add_argument("--interval", type=int, default=60,
                        help="Daemon poll interval in seconds (default: 60)")
    args = parser.parse_args()

    run_orchestrator(
        dry_run=args.dry_run,
        daemon=args.daemon,
        interval=args.interval,
    )
