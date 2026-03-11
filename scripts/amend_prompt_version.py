#!/usr/bin/env python3
"""
scripts/amend_prompt_version.py — AOS Prompt Version Splinter Agent
=====================================================================
Constitutional Role: Prompt Lineage Preservation

PURPOSE:
  On every version bump, this script:
  1. Locates the previous version's prompt file (master prompt — NEVER modified)
  2. Copies it forward to the new version filename
  3. Appends a VERSION SPLINTER section documenting what changed

  The master prompt content is always preserved verbatim at the top.
  The splinter is appended as a clearly delimited section at the bottom.
  This means every prompt file is fully self-contained AND carries its history.

SPLINTER FORMAT:
  ═══════════════════════════════════════════════════════════
  VERSION SPLINTER — v9.9.24
  Generated: 2026-03-10T17:49:00Z | Agent: Sprinter-7b
  ═══════════════════════════════════════════════════════════
  CHANGES THIS VERSION:
    - orchestrator_loop.py deployed — Phase 2 Auto-Delegator live
    - MISSION_QUEUE.json — Claude→factory interface established
    - _gate_logic traceback reporting fixed
    - opsec_rag_scout.py production deployment
  PLANS NEXT VERSION:
    - Zoo first epoch
    - TEST_1d Predatory Gate
  ═══════════════════════════════════════════════════════════

USAGE:
  # Called automatically by Makefile before forge runs
  python3 scripts/amend_prompt_version.py --version 9.9.24

  # With explicit changelog (from orchestrator_loop or run_loop)
  python3 scripts/amend_prompt_version.py --version 9.9.24 \
    --changes "orchestrator_loop deployed, gate_logic fixed" \
    --plans "Zoo first epoch, Predatory Gate"
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT    = Path(__file__).resolve().parents[1]
MISSIONS_DIR = REPO_ROOT / "prompts" / "missions"
ORCH_STATE   = REPO_ROOT / "orchestration" / "ORCHESTRATOR_STATE.json"
DECISION_LOG = REPO_ROOT / "docs" / "DECISION_LOG.md"

SPLINTER_DELIMITER = "═" * 63


def find_previous_prompt(new_version: str) -> Path | None:
    """Find the most recent prompt file older than new_version."""
    pattern = "TRADER_OPS_MASTER_IDE_REQUEST_v*.txt"
    candidates = sorted(MISSIONS_DIR.glob(pattern))

    # Filter out the new version itself if it somehow exists
    candidates = [p for p in candidates if new_version not in p.name]

    if not candidates:
        return None

    # Return the last one (highest version by sort)
    return candidates[-1]


def read_orchestrator_changes() -> tuple[list[str], list[str]]:
    """Extract recent mission completions from ORCHESTRATOR_STATE.json."""
    changes = []
    plans = []

    if ORCH_STATE.exists():
        try:
            state = json.loads(ORCH_STATE.read_text())
            for run in state.get("runs", [])[-3:]:  # last 3 runs
                for mid in run.get("ratifications_pending", []):
                    changes.append(f"Mission ratified: {mid}")
        except Exception:
            pass

    # Read pending missions from queue as plans
    queue_path = REPO_ROOT / "orchestration" / "MISSION_QUEUE.json"
    if queue_path.exists():
        try:
            queue = json.loads(queue_path.read_text())
            for m in queue.get("missions", []):
                if m.get("status") == "PENDING":
                    plans.append(f"{m['domain']}: {m['task']}")
        except Exception:
            pass

    return changes, plans


def build_splinter(version: str, changes: list[str], plans: list[str]) -> str:
    """Build the version splinter block."""
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    lines = [
        "",
        SPLINTER_DELIMITER,
        f"VERSION SPLINTER — v{version}",
        f"Generated: {timestamp} | Agent: amend_prompt_version.py",
        SPLINTER_DELIMITER,
        "",
        "CHANGES THIS VERSION:",
    ]

    if changes:
        for c in changes:
            lines.append(f"  - {c}")
    else:
        lines.append("  - (no orchestrator state found — manual bump)")

    lines.append("")
    lines.append("PLANS NEXT VERSION:")

    if plans:
        for p in plans:
            lines.append(f"  - {p}")
    else:
        lines.append("  - (see MISSION_QUEUE.json for current queue)")

    lines.append("")
    lines.append(SPLINTER_DELIMITER)
    lines.append("")

    return "\n".join(lines)


def amend(version: str,
          changes: list[str] | None = None,
          plans: list[str] | None = None,
          dry_run: bool = False) -> Path:
    """
    Main entry point. Returns the path to the new/amended prompt file.
    """
    new_path = MISSIONS_DIR / f"TRADER_OPS_MASTER_IDE_REQUEST_v{version}.txt"

    # If file already exists and already has a splinter for this version — skip
    if new_path.exists():
        content = new_path.read_text()
        if f"VERSION SPLINTER — v{version}" in content:
            print(f"Splinter already present in {new_path.name} — skipping.")
            return new_path
        else:
            # File exists but no splinter yet — just append
            print(f"Appending splinter to existing {new_path.name}")
    else:
        # File doesn't exist — copy from previous version first
        prev = find_previous_prompt(version)
        if prev is None:
            print("ERROR: No previous prompt file found to copy from.", file=sys.stderr)
            sys.exit(1)

        print(f"Copying {prev.name} → {new_path.name}")
        if not dry_run:
            new_path.write_text(prev.read_text())

    # Build splinter
    auto_changes, auto_plans = read_orchestrator_changes()
    final_changes = changes if changes is not None else auto_changes
    final_plans   = plans   if plans   is not None else auto_plans

    splinter = build_splinter(version, final_changes, final_plans)

    print(f"Appending VERSION SPLINTER — v{version}")
    if not dry_run:
        with open(new_path, "a") as f:
            f.write(splinter)

    print(f"✅ Prompt file ready: {new_path.name}")
    return new_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="AOS Prompt Version Splinter Agent"
    )
    parser.add_argument("--version", required=True,
                        help="New version string e.g. 9.9.24")
    parser.add_argument("--changes", default=None,
                        help="Comma-separated list of changes this version")
    parser.add_argument("--plans", default=None,
                        help="Comma-separated list of plans for next version")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would happen without writing files")
    args = parser.parse_args()

    changes = [c.strip() for c in args.changes.split(",")] if args.changes else None
    plans   = [p.strip() for p in args.plans.split(",")]   if args.plans   else None

    amend(args.version, changes=changes, plans=plans, dry_run=args.dry_run)
