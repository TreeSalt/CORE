#!/usr/bin/env python3
"""
core_cli_epoch.py — CORE Epoch & Mission Lifecycle CLI Extensions
==================================================================
Version: 1.0.0
License: Proprietary — TreeSalt/CORE
Author: Hostile Auditor (Claude) per Sovereign Q-T8 ratification, 2026-05-13
Anchored to: CORE_v4_Manifesto_Skeleton_v0_26.md

Adds three subcommands to the `core` CLI:

  core epoch open <epoch-id> --name <epoch-name> [--from <manifest-file>]
      Create fresh MISSION_QUEUE.json + epoch scaffolding. Optional --from
      reads a manifest specification (SKELETON_SPLIT_STRATEGY.md format
      OR a custom JSON manifest) and pre-populates mission entries.

  core mission ingest <prompt-file> [--id <mission-id>] [--track <track>]
      Ingest a free-form Sovereign prompt OR a structured drafting brief
      and generate the corresponding mission entry. Creates
      prompts/missions/mission_<id>.md skeleton with MANIFEST block and
      appends entry to MISSION_QUEUE.json with status=PENDING.

  core epoch close [--force]
      Validate all missions are in terminal state, generate summary
      report with counts per status, create EXODUS manifest with
      BLAKE3 chain anchoring, archive MISSION_QUEUE.json to versioned
      snapshot. Refuses to close if non-terminal missions remain unless
      --force is specified.

ARCHITECTURAL INVARIANTS PRESERVED:
  - All operations dry-run-able for Sovereign preview
  - Every state mutation cryptographically anchored to BLAKE3 chain
  - Deterministic preflight gates before any mutation
  - No LLM invocation; pure algorithmic state management
  - Composes with existing core_cli.py + core_cli_extensions.py via the
    same register_subparsers + COMMAND_HANDLERS pattern

INTEGRATION (in core_cli.py argparse setup):
    from core_cli_epoch import (
        register_subparsers as _register_epoch,
        COMMAND_HANDLERS as _EPOCH_HANDLERS,
    )
    _register_epoch(subparsers)
    COMMAND_HANDLERS.update(_EPOCH_HANDLERS)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ── PATHS ─────────────────────────────────────────────────────────────────────
# Replicates the path constants from core_cli.py so this module is drop-in
REPO_ROOT = Path(__file__).resolve().parents[1]
ORCH_DIR = REPO_ROOT / "orchestration"
MISSION_QUEUE = ORCH_DIR / "MISSION_QUEUE.json"
MISSION_QUEUE_ARCHIVE = ORCH_DIR / "archive"
PROMPTS_DIR = REPO_ROOT / "prompts" / "missions"
STATE_DIR = REPO_ROOT / "state"
SOVEREIGN_VAULT = STATE_DIR / "sovereign_vault"
EXODUS_DIR = SOVEREIGN_VAULT / "snapshots"
LEDGER_DIR = STATE_DIR / "ledger"
CHAIN_FILE = LEDGER_DIR / "chain.jsonl"

# ── ANSI COLORS (matches core_cli.py palette) ─────────────────────────────────
C_RESET = "\033[0m"
C_BOLD = "\033[1m"
C_RED = "\033[91m"
C_GREEN = "\033[92m"
C_YELLOW = "\033[93m"
C_BLUE = "\033[94m"
C_CYAN = "\033[96m"
C_DIM = "\033[2m"


def c(text: str, color: str) -> str:
    return f"{color}{text}{C_RESET}"


# ── TERMINAL MISSION STATES ───────────────────────────────────────────────────
TERMINAL_STATES = {
    "RATIFIED",
    "SUPERSEDED_OBSOLETE",
    "REJECTED_OBSOLETE",
    "ESCALATE",
}
PENDING_STATES = {
    "PENDING",
    "IN_PROGRESS",
    "AWAITING_RATIFICATION",
}


# ── SHARED UTILITIES ──────────────────────────────────────────────────────────

def _now_iso() -> str:
    """ISO 8601 timestamp with UTC offset."""
    return datetime.now(timezone.utc).isoformat()


def _now_epoch_id_safe() -> str:
    """Filesystem-safe timestamp for snapshot directories."""
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _blake3_hex(data: bytes) -> str:
    """
    Compute BLAKE3 hash of bytes. Falls back to SHA256 if blake3 unavailable
    (HOSTILE AUDITOR NOTE: SHA256 fallback is a deployment-time concession;
    production should ensure blake3 Python package is installed for §6.5.2
    audit chain integrity claims to hold mathematically).
    """
    try:
        import blake3  # type: ignore
        return blake3.blake3(data).hexdigest()
    except ImportError:
        return "sha256_fallback:" + hashlib.sha256(data).hexdigest()


def _read_chain_tail() -> dict[str, Any] | None:
    """Read the most recent chain entry for sequence number + prev_hash anchor."""
    if not CHAIN_FILE.exists():
        return None
    try:
        with CHAIN_FILE.open("r") as f:
            lines = [line for line in f if line.strip()]
        if not lines:
            return None
        return json.loads(lines[-1])
    except (json.JSONDecodeError, OSError) as e:
        print(c(f"WARNING: chain read failed: {e}", C_YELLOW), file=sys.stderr)
        return None


def _write_ledger_entry(event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
    """
    Append a cryptographically-chained entry to the BLAKE3 ledger.

    Schema (matches the existing chain entry format from core_cli_extensions.py
    cmd_close_mission MISSION_CLOSED_AS_OBSOLETE pattern):
      {
        "seq": N,
        "ts": ISO_TIMESTAMP,
        "event_type": str,
        "prev_hash": str | None,
        "payload": {...},
        "hash": str
      }

    The entry's `hash` is BLAKE3(canonical_json(everything except hash)).
    Returns the written entry for chained operations.
    """
    LEDGER_DIR.mkdir(parents=True, exist_ok=True)

    tail = _read_chain_tail()
    seq = (tail["seq"] + 1) if tail else 1
    prev_hash = tail["hash"] if tail else None

    entry = {
        "seq": seq,
        "ts": _now_iso(),
        "event_type": event_type,
        "prev_hash": prev_hash,
        "payload": payload,
    }
    canonical = json.dumps(entry, sort_keys=True, separators=(",", ":")).encode("utf-8")
    entry["hash"] = _blake3_hex(canonical)

    with CHAIN_FILE.open("a") as f:
        f.write(json.dumps(entry, separators=(",", ":")) + "\n")

    return entry


def _load_queue() -> dict[str, Any]:
    """Load MISSION_QUEUE.json; return empty scaffold if absent."""
    if not MISSION_QUEUE.exists():
        return {"epoch": None, "epoch_name": None, "missions": []}
    with MISSION_QUEUE.open("r") as f:
        return json.load(f)


def _save_queue(queue: dict[str, Any]) -> None:
    """Atomic write of MISSION_QUEUE.json via temp-file rename."""
    ORCH_DIR.mkdir(parents=True, exist_ok=True)
    tmp = MISSION_QUEUE.with_suffix(".json.tmp")
    with tmp.open("w") as f:
        json.dump(queue, f, indent=2, ensure_ascii=False)
        f.write("\n")
    tmp.replace(MISSION_QUEUE)


def _slugify(text: str, max_len: int = 60) -> str:
    """Convert arbitrary text to a filesystem-safe slug."""
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "_", text.strip().lower())
    slug = re.sub(r"_+", "_", slug).strip("_")
    return slug[:max_len] if slug else "untitled"


def _validate_epoch_id(epoch_id: str) -> bool:
    """Epoch IDs follow the E<N> or E<N>_<descriptor> pattern."""
    return bool(re.match(r"^E\d+(_[A-Z][A-Z0-9_]*)?$", epoch_id))


# ── COMMAND 1: core epoch open ────────────────────────────────────────────────

def cmd_epoch_open(args: argparse.Namespace) -> int:
    """
    Open a new epoch. Creates fresh MISSION_QUEUE.json with epoch metadata
    and optionally pre-populates missions from a manifest file.
    """
    epoch_id = args.epoch_id
    epoch_name = args.name
    manifest_path = Path(args.from_file) if args.from_file else None
    dry_run = args.dry_run

    if not _validate_epoch_id(epoch_id):
        print(c(f"ERROR: invalid epoch_id '{epoch_id}' — expected E<N> or E<N>_<DESCRIPTOR>", C_RED), file=sys.stderr)
        return 1

    # Refuse to overwrite active epoch unless --force
    current = _load_queue()
    if current.get("epoch") and not args.force:
        non_terminal = [m for m in current.get("missions", []) if m.get("status") not in TERMINAL_STATES]
        if non_terminal:
            print(c(f"ERROR: epoch '{current['epoch']}' has {len(non_terminal)} non-terminal missions", C_RED), file=sys.stderr)
            print(c("       close the current epoch via `core epoch close` first, OR use --force to override", C_YELLOW), file=sys.stderr)
            return 1

    # Build mission scaffolding from manifest if provided
    scaffolded_missions: list[dict[str, Any]] = []
    manifest_summary = "no manifest provided; empty epoch scaffold created"
    if manifest_path:
        if not manifest_path.exists():
            print(c(f"ERROR: manifest file not found: {manifest_path}", C_RED), file=sys.stderr)
            return 1
        try:
            scaffolded_missions, manifest_summary = _parse_manifest(manifest_path, epoch_id)
        except ValueError as e:
            print(c(f"ERROR: manifest parse failed: {e}", C_RED), file=sys.stderr)
            return 1

    # Compose the new queue
    new_queue = {
        "epoch": epoch_id,
        "epoch_name": epoch_name,
        "authored_by": "Sovereign via `core epoch open` CLI",
        "authored_at": _now_iso(),
        "missions": scaffolded_missions,
    }

    # Dry-run preview
    if dry_run:
        print(c(f"=== DRY RUN: core epoch open {epoch_id} ===", C_CYAN + C_BOLD))
        print(f"  epoch_name: {epoch_name}")
        print(f"  manifest:   {manifest_summary}")
        print(f"  missions:   {len(scaffolded_missions)} scaffolded entries")
        if scaffolded_missions:
            print(c("  mission preview (first 3):", C_DIM))
            for m in scaffolded_missions[:3]:
                print(f"    - {m['id']} [{m.get('track', 'default')}] {m.get('mission_file', '(no file)')}")
            if len(scaffolded_missions) > 3:
                print(c(f"    ... +{len(scaffolded_missions) - 3} more", C_DIM))
        print(c("\n(no state mutated; rerun without --dry-run to commit)", C_YELLOW))
        return 0

    # Archive existing queue if present (preserves audit trail)
    if MISSION_QUEUE.exists():
        MISSION_QUEUE_ARCHIVE.mkdir(parents=True, exist_ok=True)
        archive_name = f"MISSION_QUEUE_{current.get('epoch', 'UNKNOWN')}_{_now_epoch_id_safe()}.json"
        shutil.copy2(MISSION_QUEUE, MISSION_QUEUE_ARCHIVE / archive_name)
        print(c(f"  archived previous queue → {archive_name}", C_DIM))

    # Create mission_<id>.md skeleton files if scaffolded from manifest
    if scaffolded_missions and not args.no_mission_files:
        PROMPTS_DIR.mkdir(parents=True, exist_ok=True)
        for m in scaffolded_missions:
            mission_file_path = PROMPTS_DIR / m["mission_file"]
            if not mission_file_path.exists():  # don't overwrite existing
                mission_file_path.write_text(_render_mission_skeleton(m, epoch_id, epoch_name))

    # Atomic write of new queue
    _save_queue(new_queue)

    # Ledger anchor — EPOCH_OPENED event
    payload = {
        "epoch_id": epoch_id,
        "epoch_name": epoch_name,
        "mission_count": len(scaffolded_missions),
        "manifest_source": str(manifest_path) if manifest_path else None,
        "queue_hash": _blake3_hex(json.dumps(new_queue, sort_keys=True).encode("utf-8")),
    }
    entry = _write_ledger_entry("EPOCH_OPENED", payload)

    print(c(f"✓ Epoch {epoch_id} opened — {epoch_name}", C_GREEN + C_BOLD))
    print(f"  missions scaffolded: {len(scaffolded_missions)}")
    print(f"  ledger anchor:       seq={entry['seq']} hash={entry['hash'][:16]}...")
    print(f"  queue:               {MISSION_QUEUE.relative_to(REPO_ROOT)}")
    return 0


def _parse_manifest(path: Path, epoch_id: str) -> tuple[list[dict[str, Any]], str]:
    """
    Parse a manifest file into mission scaffolding entries.

    Two supported formats:
      1. JSON manifest with explicit mission entries:
         {"missions": [{"id": "...", "domain": "...", "track": "...", ...}]}

      2. SKELETON_SPLIT_STRATEGY.md format (Markdown with ### File NN: SECTION_*.md
         entries) — parsed via regex; one mission per File entry.

    Returns (mission_list, human_readable_summary).
    """
    content = path.read_text()

    # Try JSON first
    if path.suffix == ".json":
        data = json.loads(content)
        missions = data.get("missions", [])
        return _normalize_scaffolded_missions(missions, epoch_id), f"JSON manifest: {len(missions)} entries"

    # Fall back to SKELETON_SPLIT_STRATEGY.md parsing
    file_blocks = re.findall(
        r"^### File (\d+): ([A-Z0-9_]+\.md)\n(.*?)(?=^### File \d+:|^## |\Z)",
        content,
        re.MULTILINE | re.DOTALL,
    )
    if not file_blocks:
        raise ValueError("no `### File NN: FILENAME.md` entries found in markdown manifest")

    missions = []
    for file_num, filename, body in file_blocks:
        section_id = filename.replace(".md", "")
        # Extract sub-content if present (for drafter task summary)
        sub_content_match = re.search(r"\*\*Sub-content:\*\*\s*(.+?)(?=\n- \*\*|\Z)", body, re.DOTALL)
        sub_content = sub_content_match.group(1).strip() if sub_content_match else ""
        # Extract drafter
        drafter_match = re.search(r"\*\*Drafter:\*\*\s*([^\n]+)", body)
        drafter = drafter_match.group(1).strip() if drafter_match else "Forger Pool"
        # Extract skeleton lines
        lines_match = re.search(r"\*\*Skeleton lines:\*\*\s*([^\n(]+)", body)
        skeleton_lines = lines_match.group(1).strip() if lines_match else ""
        # NEW: Extract source corpus, cross-references, hostile auditor expectations
        corpus_match = re.search(r"\*\*Source corpus:\*\*\s*(.+?)(?=\n- \*\*|\Z)", body, re.DOTALL)
        source_corpus = corpus_match.group(1).strip() if corpus_match else ""
        xref_match = re.search(r"\*\*Cross-references:\*\*\s*(.+?)(?=\n- \*\*|\Z)", body, re.DOTALL)
        cross_references = xref_match.group(1).strip() if xref_match else ""
        haud_match = re.search(r"\*\*Hostile Auditor expectations:\*\*\s*(.+?)(?=\n- \*\*|\Z)", body, re.DOTALL)
        hostile_auditor_expectations = haud_match.group(1).strip() if haud_match else ""

        mission_id = f"MANIFESTO_{epoch_id}_{int(file_num):03d}_{_slugify(section_id, 40)}"
        mission_file = f"mission_{mission_id}.md"

        missions.append({
            "id": mission_id,
            "domain": "MANIFESTO_AUTHORSHIP",
            "task": mission_id,
            "mission_file": mission_file,
            "type": "DRAFTING",
            "max_retries": 3,
            "priority": int(file_num),
            "status": "PENDING",
            "track": "MANIFESTO_V4",
            "drafter": drafter,
            "section_id": section_id,
            "skeleton_lines": skeleton_lines,
            "sub_content": sub_content[:500],  # truncate for queue compactness
            "source_corpus": source_corpus,
            "cross_references": cross_references,
            "hostile_auditor_expectations": hostile_auditor_expectations,
        })

    return missions, f"SKELETON_SPLIT_STRATEGY.md: {len(missions)} File entries parsed"


def _normalize_scaffolded_missions(missions: list[dict[str, Any]], epoch_id: str) -> list[dict[str, Any]]:
    """Apply default fields to JSON-source missions."""
    normalized = []
    for i, m in enumerate(missions):
        n = dict(m)  # shallow copy
        n.setdefault("id", f"MISSION_{epoch_id}_{i:03d}_{_slugify(str(m.get('task', 'untitled')), 30)}")
        n.setdefault("status", "PENDING")
        n.setdefault("priority", i)
        n.setdefault("max_retries", 3)
        n.setdefault("type", "IMPLEMENTATION")
        n.setdefault("mission_file", f"mission_{n['id']}.md")
        normalized.append(n)
    return normalized


def _render_mission_skeleton(mission: dict[str, Any], epoch_id: str, epoch_name: str) -> str:
    """Render a mission_<id>.md skeleton with MANIFEST block + drafting brief stub."""
    return f"""# Mission: {mission['id']}

<MANIFEST>
EPOCH: {epoch_id}
EPOCH_NAME: {epoch_name}
MISSION_ID: {mission['id']}
DOMAIN: {mission.get('domain', 'UNKNOWN')}
TYPE: {mission.get('type', 'IMPLEMENTATION')}
TRACK: {mission.get('track', 'default')}
PRIORITY: {mission.get('priority', 0)}
STATUS: PENDING
DRAFTER: {mission.get('drafter', 'Forger Pool')}
SECTION_ID: {mission.get('section_id', '')}
SKELETON_LINES: {mission.get('skeleton_lines', '')}
CREATED_AT: {_now_iso()}
HOSTILE_AUDITOR_REVIEW_STATUS: PENDING
SOVEREIGN_RATIFICATION_STATUS: PENDING
</MANIFEST>

## Task

{mission.get('sub_content', '(populate task description here)')}

## Source Corpus

{mission.get('source_corpus') or '(list source documents the drafter must consult)'}

## Cross-References

{mission.get('cross_references') or '(list other mission IDs whose output this mission depends on or composes with)'}

## Hostile Auditor Expectations

{mission.get('hostile_auditor_expectations') or '(list the specific constraints the drafted output must satisfy on review; see MANIFESTO_WRITER_BRIEF.md File ' + str(mission.get('priority', '?')) + ' for the authoritative drafting brief if this is a manifesto-authorship mission)'}

## Output

(drafter populates this section with the produced work product)

---

🐈 Christ is King.
"""


# ── COMMAND 2: core mission ingest ────────────────────────────────────────────

def cmd_mission_ingest(args: argparse.Namespace) -> int:
    """
    Ingest a free-form prompt OR drafting brief and create a mission entry.
    """
    prompt_path = Path(args.prompt_file)
    dry_run = args.dry_run

    if not prompt_path.exists():
        print(c(f"ERROR: prompt file not found: {prompt_path}", C_RED), file=sys.stderr)
        return 1

    prompt_content = prompt_path.read_text()

    # Verify there is an open epoch
    queue = _load_queue()
    if not queue.get("epoch"):
        print(c("ERROR: no active epoch — run `core epoch open <epoch-id>` first", C_RED), file=sys.stderr)
        return 1

    # Determine mission ID
    if args.mission_id:
        mission_id = args.mission_id
    else:
        # Auto-derive from prompt filename
        base = prompt_path.stem
        mission_count = len(queue.get("missions", []))
        mission_id = f"INGEST_{queue['epoch']}_{mission_count:03d}_{_slugify(base, 40)}"

    # Check for ID collision
    existing_ids = {m.get("id") for m in queue.get("missions", [])}
    if mission_id in existing_ids:
        print(c(f"ERROR: mission_id '{mission_id}' already exists in queue", C_RED), file=sys.stderr)
        return 1

    track = args.track or "INGESTED"
    mission_file_name = f"mission_{mission_id}.md"

    # Build mission entry
    new_mission = {
        "id": mission_id,
        "domain": args.domain or "SOVEREIGN_INGEST",
        "task": mission_id,
        "mission_file": mission_file_name,
        "type": args.type or "IMPLEMENTATION",
        "max_retries": 3,
        "priority": args.priority if args.priority is not None else len(queue.get("missions", [])),
        "status": "PENDING",
        "track": track,
        "ingested_from": str(prompt_path),
        "ingested_at": _now_iso(),
    }

    # Dry-run preview
    if dry_run:
        print(c(f"=== DRY RUN: core mission ingest {prompt_path.name} ===", C_CYAN + C_BOLD))
        print(f"  active epoch:  {queue['epoch']} ({queue.get('epoch_name', '?')})")
        print(f"  mission_id:    {mission_id}")
        print(f"  track:         {track}")
        print(f"  domain:        {new_mission['domain']}")
        print(f"  type:          {new_mission['type']}")
        print(f"  priority:      {new_mission['priority']}")
        print(f"  mission_file:  prompts/missions/{mission_file_name}")
        print(c(f"  prompt content preview ({len(prompt_content)} chars):", C_DIM))
        for line in prompt_content.splitlines()[:5]:
            print(c(f"    | {line}", C_DIM))
        if len(prompt_content.splitlines()) > 5:
            print(c(f"    | ... +{len(prompt_content.splitlines()) - 5} more lines", C_DIM))
        print(c("\n(no state mutated; rerun without --dry-run to commit)", C_YELLOW))
        return 0

    # Create mission_<id>.md file
    PROMPTS_DIR.mkdir(parents=True, exist_ok=True)
    mission_file_path = PROMPTS_DIR / mission_file_name

    mission_md_content = f"""# Mission: {mission_id}

<MANIFEST>
EPOCH: {queue['epoch']}
EPOCH_NAME: {queue.get('epoch_name', '')}
MISSION_ID: {mission_id}
DOMAIN: {new_mission['domain']}
TYPE: {new_mission['type']}
TRACK: {track}
PRIORITY: {new_mission['priority']}
STATUS: PENDING
INGESTED_FROM: {prompt_path}
INGESTED_AT: {new_mission['ingested_at']}
HOSTILE_AUDITOR_REVIEW_STATUS: PENDING
SOVEREIGN_RATIFICATION_STATUS: PENDING
</MANIFEST>

## Sovereign Prompt (verbatim from source)

{prompt_content}

## Output

(drafter populates this section with the produced work product)

---

🐈 Christ is King.
"""
    mission_file_path.write_text(mission_md_content)

    # Append to queue
    queue["missions"].append(new_mission)
    _save_queue(queue)

    # Ledger anchor
    payload = {
        "epoch_id": queue["epoch"],
        "mission_id": mission_id,
        "track": track,
        "ingested_from": str(prompt_path),
        "prompt_hash": _blake3_hex(prompt_content.encode("utf-8")),
    }
    entry = _write_ledger_entry("MISSION_INGESTED", payload)

    print(c(f"✓ Mission ingested: {mission_id}", C_GREEN + C_BOLD))
    print(f"  epoch:         {queue['epoch']}")
    print(f"  mission file:  {mission_file_path.relative_to(REPO_ROOT)}")
    print(f"  ledger anchor: seq={entry['seq']} hash={entry['hash'][:16]}...")
    return 0


# ── COMMAND 3: core epoch close ───────────────────────────────────────────────

def cmd_epoch_close(args: argparse.Namespace) -> int:
    """
    Validate all missions in terminal state, generate summary, create EXODUS
    snapshot with BLAKE3 anchor, archive queue.
    """
    dry_run = args.dry_run
    force = args.force

    queue = _load_queue()
    epoch_id = queue.get("epoch")
    epoch_name = queue.get("epoch_name", "")

    if not epoch_id:
        print(c("ERROR: no active epoch to close", C_RED), file=sys.stderr)
        return 1

    missions = queue.get("missions", [])

    # Validate terminal-state requirement
    status_counts: dict[str, int] = {}
    non_terminal: list[dict[str, Any]] = []
    for m in missions:
        status = m.get("status", "UNKNOWN")
        status_counts[status] = status_counts.get(status, 0) + 1
        if status not in TERMINAL_STATES:
            non_terminal.append(m)

    if non_terminal and not force:
        print(c(f"ERROR: epoch '{epoch_id}' has {len(non_terminal)} non-terminal missions:", C_RED), file=sys.stderr)
        for m in non_terminal[:10]:
            print(c(f"  - {m['id']} [{m.get('status', 'UNKNOWN')}]", C_YELLOW), file=sys.stderr)
        if len(non_terminal) > 10:
            print(c(f"  ... +{len(non_terminal) - 10} more", C_YELLOW), file=sys.stderr)
        print(c("\n       resolve to RATIFIED / SUPERSEDED_OBSOLETE / REJECTED_OBSOLETE / ESCALATE, OR use --force", C_YELLOW), file=sys.stderr)
        return 1

    # Build the summary report
    summary = {
        "epoch_id": epoch_id,
        "epoch_name": epoch_name,
        "authored_by": queue.get("authored_by"),
        "authored_at": queue.get("authored_at"),
        "closed_at": _now_iso(),
        "mission_total": len(missions),
        "status_counts": status_counts,
        "non_terminal_at_close": len(non_terminal),
        "force_close": force and bool(non_terminal),
    }

    # Dry-run preview
    if dry_run:
        print(c(f"=== DRY RUN: core epoch close {epoch_id} ===", C_CYAN + C_BOLD))
        print(f"  epoch_name:  {epoch_name}")
        print(f"  total missions: {summary['mission_total']}")
        print(c("  status breakdown:", C_DIM))
        for status, count in sorted(status_counts.items()):
            color = C_GREEN if status in TERMINAL_STATES else C_YELLOW
            print(f"    {c(status, color):30s} {count}")
        if non_terminal:
            print(c(f"  WARNING: {len(non_terminal)} non-terminal missions present", C_YELLOW))
            print(c(f"           --force is {'SET' if force else 'NOT SET'}", C_RED if not force else C_YELLOW))
        print(c("\n(no state mutated; rerun without --dry-run to commit)", C_YELLOW))
        return 0

    # Create EXODUS manifest directory
    exodus_name = f"EXODUS_{epoch_id}_{_now_epoch_id_safe()}"
    exodus_path = EXODUS_DIR / exodus_name
    exodus_path.mkdir(parents=True, exist_ok=True)

    # Write summary + queue snapshot to EXODUS
    summary_file = exodus_path / "summary.json"
    summary_file.write_text(json.dumps(summary, indent=2) + "\n")

    queue_snapshot = exodus_path / "MISSION_QUEUE_at_close.json"
    queue_snapshot.write_text(json.dumps(queue, indent=2, ensure_ascii=False) + "\n")

    # Compute manifest hash (BLAKE3 over summary + queue)
    manifest_bytes = (summary_file.read_bytes() + queue_snapshot.read_bytes())
    manifest_hash = _blake3_hex(manifest_bytes)

    manifest_json = {
        "manifest_version": "1.0",
        "epoch_id": epoch_id,
        "epoch_name": epoch_name,
        "exodus_name": exodus_name,
        "created_at": _now_iso(),
        "summary_file": "summary.json",
        "queue_snapshot_file": "MISSION_QUEUE_at_close.json",
        "manifest_hash_blake3": manifest_hash,
        "summary": summary,
    }
    manifest_file = exodus_path / "manifest.json"
    manifest_file.write_text(json.dumps(manifest_json, indent=2) + "\n")

    # Archive MISSION_QUEUE.json itself
    MISSION_QUEUE_ARCHIVE.mkdir(parents=True, exist_ok=True)
    archive_name = f"MISSION_QUEUE_{epoch_id}_CLOSED_{_now_epoch_id_safe()}.json"
    shutil.copy2(MISSION_QUEUE, MISSION_QUEUE_ARCHIVE / archive_name)

    # Ledger anchor
    payload = {
        "epoch_id": epoch_id,
        "epoch_name": epoch_name,
        "exodus_path": str(exodus_path.relative_to(REPO_ROOT)),
        "manifest_hash": manifest_hash,
        "status_counts": status_counts,
        "force_close": summary["force_close"],
    }
    entry = _write_ledger_entry("EPOCH_CLOSED", payload)

    # Render summary
    print(c(f"✓ Epoch {epoch_id} closed — {epoch_name}", C_GREEN + C_BOLD))
    print(f"  total missions: {summary['mission_total']}")
    print(c("  status breakdown:", C_DIM))
    for status, count in sorted(status_counts.items()):
        color = C_GREEN if status in TERMINAL_STATES else C_YELLOW
        print(f"    {c(status, color):30s} {count}")
    print(f"  EXODUS manifest: {exodus_path.relative_to(REPO_ROOT)}")
    print(f"  manifest hash:   {manifest_hash[:32]}...")
    print(f"  ledger anchor:   seq={entry['seq']} hash={entry['hash'][:16]}...")
    print(f"  queue archived:  {archive_name}")
    if summary["force_close"]:
        print(c(f"\n  ⚠  WARNING: force-closed with {len(non_terminal)} non-terminal missions", C_YELLOW + C_BOLD))

    return 0


# ── SUBPARSER REGISTRATION ────────────────────────────────────────────────────

def register_subparsers(subparsers: argparse._SubParsersAction) -> None:
    """Hook into core_cli.py's argparse subparsers."""
    # `core epoch ...`
    epoch_parser = subparsers.add_parser("epoch", help="Epoch lifecycle management (open/close)")
    epoch_sub = epoch_parser.add_subparsers(dest="epoch_action", required=True)

    # `core epoch open`
    open_parser = epoch_sub.add_parser("open", help="Open a new epoch with optional mission scaffolding")
    open_parser.add_argument("epoch_id", help="Epoch ID (E<N> or E<N>_<DESCRIPTOR>)")
    open_parser.add_argument("--name", required=True, help="Human-readable epoch name")
    open_parser.add_argument("--from", dest="from_file", default=None,
                             help="Manifest file (SKELETON_SPLIT_STRATEGY.md or JSON) for mission scaffolding")
    open_parser.add_argument("--no-mission-files", action="store_true",
                             help="Skip mission_<id>.md skeleton file creation (queue-only)")
    open_parser.add_argument("--force", action="store_true",
                             help="Force open even if current epoch has non-terminal missions")
    open_parser.add_argument("--dry-run", action="store_true", help="Preview without mutating state")

    # `core epoch close`
    close_parser = epoch_sub.add_parser("close", help="Close the active epoch, generate EXODUS manifest")
    close_parser.add_argument("--force", action="store_true",
                              help="Force close even if non-terminal missions remain")
    close_parser.add_argument("--dry-run", action="store_true", help="Preview without mutating state")

    # `core mission ingest`
    mission_parser = subparsers.add_parser("mission", help="Mission lifecycle management")
    mission_sub = mission_parser.add_subparsers(dest="mission_action", required=True)

    ingest_parser = mission_sub.add_parser("ingest", help="Ingest a prompt file into the active epoch")
    ingest_parser.add_argument("prompt_file", help="Path to the prompt/brief file to ingest")
    ingest_parser.add_argument("--id", dest="mission_id", default=None,
                               help="Explicit mission ID (auto-derived from filename if omitted)")
    ingest_parser.add_argument("--track", default=None, help="Track label (default: INGESTED)")
    ingest_parser.add_argument("--domain", default=None, help="Domain label (default: SOVEREIGN_INGEST)")
    ingest_parser.add_argument("--type", default=None, help="Mission type (default: IMPLEMENTATION)")
    ingest_parser.add_argument("--priority", type=int, default=None, help="Priority (default: append)")
    ingest_parser.add_argument("--dry-run", action="store_true", help="Preview without mutating state")


# ── COMMAND HANDLER DISPATCH ──────────────────────────────────────────────────

def _dispatch_epoch(args: argparse.Namespace) -> int:
    """Route `core epoch <action>` to the right handler."""
    if args.epoch_action == "open":
        return cmd_epoch_open(args)
    elif args.epoch_action == "close":
        return cmd_epoch_close(args)
    else:
        print(c(f"ERROR: unknown epoch action: {args.epoch_action}", C_RED), file=sys.stderr)
        return 1


def _dispatch_mission(args: argparse.Namespace) -> int:
    """Route `core mission <action>` to the right handler."""
    if args.mission_action == "ingest":
        return cmd_mission_ingest(args)
    else:
        print(c(f"ERROR: unknown mission action: {args.mission_action}", C_RED), file=sys.stderr)
        return 1


COMMAND_HANDLERS = {
    "epoch": _dispatch_epoch,
    "mission": _dispatch_mission,
}


# ── STANDALONE INVOCATION (for testing without core_cli.py integration) ───────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="core_cli_epoch",
        description="CORE Epoch & Mission Lifecycle CLI (standalone test mode)",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    register_subparsers(subparsers)
    args = parser.parse_args()
    handler = COMMAND_HANDLERS.get(args.command)
    if not handler:
        print(c(f"ERROR: unknown command: {args.command}", C_RED), file=sys.stderr)
        sys.exit(1)
    sys.exit(handler(args))
