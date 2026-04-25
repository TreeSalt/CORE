#!/usr/bin/env python3
"""
core_cli_extensions.py — New CLI commands for CORE
====================================================
Sovereign: Alec Sanchez
Auditor: Claude — Hostile Auditor
Source: Sovereign injection

Adds two new commands to the CORE CLI:
  - core doctor              Comprehensive system diagnostics
  - core stop --daemon       Cleanly stop the orchestrator daemon
  - core stop --all          Stop daemon + unload all models

This module is imported by scripts/core_cli.py. See the patch instructions
at the bottom of this file for wiring it in.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import signal
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

# ─── PATHS ───────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "scripts"
ORCH_DIR = REPO_ROOT / "orchestration"
MISSION_QUEUE = ORCH_DIR / "MISSION_QUEUE.json"
DAEMON_PID_FILE = REPO_ROOT / "wilderness_daemon.pid"
VAULT_P = REPO_ROOT / "state" / "sovereign_vault"
VAULT_R = REPO_ROOT / "dist" / "sovereign_vault"
KEY_INVENTORY = VAULT_P / "key_inventory" / "sovereign_keys_inventory.json"
GOVERNANCE = REPO_ROOT / "04_GOVERNANCE"

OLLAMA_URL = "http://localhost:11434"

# ─── ANSI COLORS ─────────────────────────────────────────────

C_RESET = "\033[0m"
C_BOLD = "\033[1m"
C_RED = "\033[91m"
C_GREEN = "\033[92m"
C_YELLOW = "\033[93m"
C_CYAN = "\033[96m"
C_DIM = "\033[2m"


def c(text: str, color: str) -> str:
    return f"{color}{text}{C_RESET}"


# ─── DIAGNOSTIC CHECKS ───────────────────────────────────────

def _check_ollama() -> tuple[bool, str, str]:
    """Returns (passed, summary, remediation)."""
    try:
        req = urllib.request.Request(f"{OLLAMA_URL}/api/tags")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
            count = len(data.get("models", []))
            return (True, f"reachable, {count} models available", "")
    except Exception as e:
        return (False, f"unreachable: {e}", "Run: systemctl --user restart ollama")


def _check_vram() -> tuple[bool, str, str]:
    """Returns (passed, summary, remediation)."""
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.total,memory.used,memory.free",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode != 0:
            return (False, "nvidia-smi failed", "Check GPU driver installation")
        parts = result.stdout.strip().split(",")
        total = int(parts[0].strip())
        used = int(parts[1].strip())
        free = int(parts[2].strip())
        pct = (used / total) * 100 if total > 0 else 0

        # Check loaded models
        loaded = []
        try:
            req = urllib.request.Request(f"{OLLAMA_URL}/api/ps")
            with urllib.request.urlopen(req, timeout=3) as resp:
                ps = json.loads(resp.read())
                loaded = [m.get("name", "") for m in ps.get("models", [])]
        except Exception:
            pass

        loaded_str = f"loaded: {', '.join(loaded)}" if loaded else "no models loaded"
        summary = f"{used}MB/{total}MB ({pct:.0f}%), {free}MB free | {loaded_str}"

        if pct > 90:
            return (False, summary,
                    "VRAM critical — run 'core vram unload' to free memory")
        if pct > 75:
            return (True, summary + " ⚠️  high",
                    "Consider unloading models before dispatching new tier")
        return (True, summary, "")
    except Exception as e:
        return (False, f"error: {e}", "Check nvidia-smi availability")


def _check_chain_integrity() -> tuple[bool, str, str]:
    """Walk the ledger chain and verify every parent_hash."""
    month = datetime.now(timezone.utc).strftime("%Y_%m")
    ledger = VAULT_P / "ledger" / f"ledger_{month}.jsonl"
    if not ledger.exists():
        return (False, f"current ledger missing ({ledger.name})",
                "Verify state/sovereign_vault/ledger/ structure")

    try:
        lines = [l for l in ledger.read_text().split("\n") if l.strip()]
        entries = [json.loads(l) for l in lines]
    except Exception as e:
        return (False, f"ledger parse error: {e}",
                "Check ledger JSON syntax — corruption may be present")

    broken = 0
    first_break = None
    for i, e in enumerate(entries):
        expected = entries[i - 1].get("entry_hash") if i > 0 else None
        if e.get("parent_hash") != expected:
            broken += 1
            if first_break is None:
                first_break = i

    if broken == 0:
        return (True, f"INTACT at {len(entries)} entries", "")
    return (False, f"{broken} breaks (first at entry {first_break})",
            "Investigate ledger tampering or run rollback to last good snapshot")


def _check_queue_health() -> tuple[bool, str, str]:
    """Survey queue status distribution."""
    if not MISSION_QUEUE.exists():
        return (False, "MISSION_QUEUE.json missing",
                "Initialize queue or restore from backup")
    try:
        queue = json.loads(MISSION_QUEUE.read_text())
        counts = {}
        for m in queue.get("missions", []):
            s = m.get("status", "UNKNOWN")
            counts[s] = counts.get(s, 0) + 1

        parts = [f"{n} {s}" for s, n in sorted(counts.items())]
        summary = " | ".join(parts) if parts else "empty"

        # Health rules: stuck IN_PROGRESS without started_at, all ESCALATE, etc
        in_progress = counts.get("IN_PROGRESS", 0)
        escalate = counts.get("ESCALATE", 0)
        total = sum(counts.values())

        # STALE_IN_PROGRESS_MARKER_v1
        warnings = []
        if escalate > total * 0.3 and total > 5:
            warnings.append("high ESCALATE ratio")

        # IN_PROGRESS is only valid when a live daemon owns the missions.
        # If no daemon is alive, ANY IN_PROGRESS is stale crash residue.
        daemon_alive = False
        if DAEMON_PID_FILE.exists():
            try:
                pid = int(DAEMON_PID_FILE.read_text().strip())
                os.kill(pid, 0)
                daemon_alive = True
            except (ProcessLookupError, ValueError, PermissionError):
                daemon_alive = False
        if in_progress > 0 and not daemon_alive:
            warnings.append(
                f"{in_progress} IN_PROGRESS but no live daemon (stale)"
            )
        elif in_progress > 3:
            warnings.append(
                f"{in_progress} IN_PROGRESS may be stuck (multi-IN_PROGRESS"
                " is invalid until Forger/Oracle ships)"
            )

        if warnings:
            remediation = "Run 'core queue reset-failed' or check daemon status"
            if any("stale" in w for w in warnings):
                remediation = "Run 'core stop --reap' to clear stale IN_PROGRESS"
            return (True, f"{summary}  ⚠️  " + ", ".join(warnings),
                    remediation)
        return (True, summary, "")
    except Exception as e:
        return (False, f"queue read error: {e}", "Restore queue from backup")


def _check_daemon() -> tuple[bool, str, str]:
    """Check if the orchestrator daemon is running."""
    if not DAEMON_PID_FILE.exists():
        return (True, "no daemon PID file (daemon not started)",
                "Start with 'core run --daemon' if intended")
    try:
        pid = int(DAEMON_PID_FILE.read_text().strip())
    except Exception:
        return (False, "PID file corrupt",
                "Remove wilderness_daemon.pid and restart")

    # Check if process exists
    try:
        os.kill(pid, 0)  # signal 0 = check existence
        # Verify it's actually our daemon, not a recycled PID
        try:
            with open(f"/proc/{pid}/cmdline", "rb") as f:
                cmdline = f.read().decode("utf-8", errors="replace")
            if "orchestrator_loop" in cmdline:
                return (True, f"running (PID {pid})", "")
            else:
                return (False, f"PID {pid} alive but not orchestrator_loop",
                        "Stale PID file — remove wilderness_daemon.pid")
        except FileNotFoundError:
            return (False, f"PID {pid} alive but /proc unreadable",
                    "Verify process identity manually")
    except ProcessLookupError:
        return (False, f"PID {pid} not running (stale PID file)",
                "Remove wilderness_daemon.pid before restarting")
    except PermissionError:
        return (True, f"PID {pid} exists (different user)", "")


def _check_keys() -> tuple[bool, str, str]:
    """Verify the three sovereign keys are accessible."""
    if not KEY_INVENTORY.exists():
        return (False, f"key inventory missing at {KEY_INVENTORY.name}",
                "Run sovereign key bootstrap")
    try:
        inventory = json.loads(KEY_INVENTORY.read_text())
        keys = inventory.get("keys", [])
    except Exception as e:
        return (False, f"inventory parse error: {e}",
                "Check key inventory JSON")

    missing = []
    found = []
    for k in keys:
        role = k.get("role", "?")
        pubkey_path = Path(k.get("pubkey_path", ""))
        if pubkey_path.exists():
            found.append(role)
        else:
            missing.append(role)

    if missing:
        return (False, f"missing keys: {missing}",
                "Restore keys from offline backup")
    return (True, f"all keys accessible: {', '.join(found)}", "")


def _check_disk_space() -> tuple[bool, str, str]:
    """Check available disk space on critical directories."""
    try:
        result = subprocess.run(
            ["df", "-BM", "--output=avail", str(REPO_ROOT)],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode != 0:
            return (False, "df failed", "Check filesystem")
        # Skip header line
        lines = result.stdout.strip().split("\n")
        avail_str = lines[-1].strip().rstrip("M")
        avail_mb = int(avail_str)
        avail_gb = avail_mb / 1024

        if avail_mb < 500:
            return (False, f"{avail_gb:.1f} GB free",
                    "Disk critical — clean up before continuing")
        if avail_mb < 5000:
            return (True, f"{avail_gb:.1f} GB free  ⚠️  low",
                    "Consider cleaning old proposals/snapshots")
        return (True, f"{avail_gb:.1f} GB free", "")
    except Exception as e:
        return (False, f"error: {e}", "Check df availability")


def _check_governor_seal() -> tuple[bool, str, str]:
    """Verify constitutional integrity hashes match the seal."""
    seal = REPO_ROOT / ".governor_seal"
    aec = GOVERNANCE / "AGENTIC_ETHICAL_CONSTITUTION.md"
    oi = GOVERNANCE / "OPERATOR_INSTANCE.yaml"

    if not seal.exists():
        return (False, "GOVERNOR_SEAL missing",
                "Constitutional integrity unverifiable — restore .governor_seal")
    if not aec.exists() or not oi.exists():
        return (False, "constitution files missing",
                "Restore 04_GOVERNANCE/ from backup")

    try:
        stored = {}
        for line in seal.read_text().splitlines():
            if line.startswith("AEC_HASH:"):
                stored["aec"] = line.split(":", 1)[1].strip()
            elif line.startswith("OI_HASH:"):
                stored["oi"] = line.split(":", 1)[1].strip()

        actual_aec = hashlib.sha256(aec.read_bytes()).hexdigest()
        actual_oi = hashlib.sha256(oi.read_bytes()).hexdigest()

        if actual_aec != stored.get("aec"):
            return (False, "AEC hash mismatch",
                    "Constitution modified without re-seal — investigate")
        if actual_oi != stored.get("oi"):
            return (False, "OI hash mismatch",
                    "OperatorInstance modified without re-seal — investigate")
        return (True, "constitutional hashes match seal", "")
    except Exception as e:
        return (False, f"seal verification error: {e}",
                "Manually verify .governor_seal and constitution files")


# ─── DOCTOR COMMAND ──────────────────────────────────────────

def cmd_doctor(args):
    """Run comprehensive diagnostic checks across CORE."""
    print()
    print(c("═" * 68, C_BOLD))
    print(c("  CORE DOCTOR — System Diagnostics", C_BOLD))
    print(c("═" * 68, C_BOLD))
    print()

    checks = [
        ("Ollama Reachability",   _check_ollama),
        ("VRAM State",            _check_vram),
        ("Chain Integrity",       _check_chain_integrity),
        ("Queue Health",          _check_queue_health),
        ("Daemon Process",        _check_daemon),
        ("Sovereign Keys",        _check_keys),
        ("Disk Space",            _check_disk_space),
        ("Governor Seal",         _check_governor_seal),
    ]

    results = []
    fail_count = 0
    for name, check_fn in checks:
        try:
            passed, summary, remediation = check_fn()
        except Exception as e:
            passed, summary, remediation = (False, f"check raised: {e}",
                                             "Investigate the doctor implementation")
        icon = c("✅ PASS", C_GREEN) if passed else c("❌ FAIL", C_RED)
        print(f"  {icon}  {c(name, C_BOLD):<40}  {summary}")
        if not passed:
            fail_count += 1
            if remediation:
                print(f"          {c('→ ' + remediation, C_DIM)}")
        elif remediation:
            # Pass with warning
            print(f"          {c('→ ' + remediation, C_DIM)}")
        results.append({"name": name, "passed": passed,
                        "summary": summary, "remediation": remediation})

    print()
    print(c("─" * 68, C_DIM))
    if fail_count == 0:
        print(c(f"  ✅ ALL CHECKS PASSED ({len(checks)}/{len(checks)})", C_GREEN))
    else:
        passed = len(checks) - fail_count
        print(c(f"  ⚠️  {passed}/{len(checks)} checks passed, "
                f"{fail_count} failed", C_YELLOW))
    print()

    return 0 if fail_count == 0 else 1


# ─── STOP COMMAND ────────────────────────────────────────────

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _parent_hash() -> str | None:
    month = datetime.now(timezone.utc).strftime("%Y_%m")
    p = VAULT_P / "ledger" / f"ledger_{month}.jsonl"
    if not p.exists():
        return None
    lines = [l for l in p.read_text().strip().split("\n") if l]
    if not lines:
        return None
    try:
        return json.loads(lines[-1]).get("entry_hash")
    except Exception:
        return None


def _write_ledger_entry(entry: dict) -> str:
    entry["parent_hash"] = _parent_hash()
    canonical = json.dumps(entry, sort_keys=True).encode()
    entry["entry_hash"] = _sha(canonical)
    line = json.dumps(entry) + "\n"
    month = datetime.now(timezone.utc).strftime("%Y_%m")
    for v in (VAULT_P, VAULT_R):
        ledger_dir = v / "ledger"
        ledger_dir.mkdir(parents=True, exist_ok=True)
        with open(ledger_dir / f"ledger_{month}.jsonl", "a") as f:
            f.write(line)
    return entry["entry_hash"]


def _stop_daemon(verbose: bool = True) -> dict:
    """Stop the orchestrator daemon. Returns status dict."""
    result = {
        "stopped": False,
        "pid": None,
        "stale_in_progress_reset": [],
        "ledger_entry": None,
        "message": "",
    }

    if not DAEMON_PID_FILE.exists():
        result["message"] = "no daemon PID file — daemon not running"
        if verbose:
            print(c("  ℹ️  No daemon PID file found.", C_DIM))
        return result

    try:
        pid = int(DAEMON_PID_FILE.read_text().strip())
        result["pid"] = pid
    except Exception as e:
        result["message"] = f"PID file corrupt: {e}"
        if verbose:
            print(c(f"  ❌ PID file corrupt: {e}", C_RED))
        return result

    # Verify process exists before signalling
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        result["message"] = f"PID {pid} not running (stale PID file)"
        if verbose:
            print(c(f"  ℹ️  PID {pid} not running. Removing stale PID file.", C_DIM))
        try:
            DAEMON_PID_FILE.unlink()
        except Exception:
            pass
        return result
    except PermissionError:
        result["message"] = f"cannot signal PID {pid} (different user)"
        if verbose:
            print(c(f"  ❌ Cannot signal PID {pid} — different user", C_RED))
        return result

    # Send SIGTERM, wait for graceful shutdown
    if verbose:
        print(c(f"  Sending SIGTERM to PID {pid}...", C_DIM))
    try:
        os.kill(pid, signal.SIGTERM)
    except Exception as e:
        result["message"] = f"SIGTERM failed: {e}"
        return result

    # Wait up to 10 seconds for graceful exit
    for i in range(10):
        time.sleep(1)
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            break
    else:
        # Still alive after 10s — escalate to SIGKILL
        if verbose:
            print(c(f"  ⚠️  Process still alive after 10s, sending SIGKILL", C_YELLOW))
        try:
            os.kill(pid, signal.SIGKILL)
            time.sleep(2)
        except Exception:
            pass

    result["stopped"] = True

    # Remove PID file
    try:
        DAEMON_PID_FILE.unlink()
    except Exception:
        pass

    # Reset any stale IN_PROGRESS missions
    if MISSION_QUEUE.exists():
        try:
            queue = json.loads(MISSION_QUEUE.read_text())
            reset = []
            for m in queue.get("missions", []):
                if m.get("status") == "IN_PROGRESS":
                    m["status"] = "PENDING"
                    m["last_revert_at"] = _now_iso()
                    m["last_revert_reason"] = "daemon_stopped_via_core_stop"
                    reset.append(m.get("id", "?"))
            if reset:
                MISSION_QUEUE.write_text(json.dumps(queue, indent=2))
                result["stale_in_progress_reset"] = reset
                if verbose:
                    print(c(f"  ✅ Reset {len(reset)} stale IN_PROGRESS missions", C_GREEN))
                    for mid in reset:
                        print(c(f"     → {mid}", C_DIM))
        except Exception as e:
            if verbose:
                print(c(f"  ⚠️  Could not reset IN_PROGRESS missions: {e}", C_YELLOW))

    # Log STOP event
    try:
        entry_hash = _write_ledger_entry({
            "ts": _now_iso(),
            "actor": "core_stop_cli",
            "action": "DAEMON_STOPPED",
            "pid": pid,
            "in_progress_reset": result["stale_in_progress_reset"],
            "result": "SUCCESS",
        })
        result["ledger_entry"] = entry_hash
        if verbose:
            print(c(f"  ✅ Ledger entry: {entry_hash[:32]}...", C_GREEN))
    except Exception as e:
        if verbose:
            print(c(f"  ⚠️  Could not write ledger entry: {e}", C_YELLOW))

    if verbose:
        print(c(f"  ✅ Daemon stopped (PID {pid})", C_GREEN))
    result["message"] = f"daemon stopped (PID {pid})"
    return result


def _unload_all_ollama_models(verbose: bool = True) -> list[str]:
    """Unload every loaded Ollama model. Returns list of unloaded names."""
    try:
        req = urllib.request.Request(f"{OLLAMA_URL}/api/ps")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
            loaded = [m.get("name", "") for m in data.get("models", [])]
    except Exception:
        loaded = []

    if not loaded:
        if verbose:
            print(c("  ℹ️  No models loaded.", C_DIM))
        return []

    unloaded = []
    for name in loaded:
        try:
            subprocess.run(["ollama", "stop", name],
                           capture_output=True, timeout=30)
            unloaded.append(name)
            if verbose:
                print(c(f"  ✅ Unloaded {name}", C_GREEN))
        except Exception as e:
            if verbose:
                print(c(f"  ⚠️  Failed to unload {name}: {e}", C_YELLOW))
    return unloaded



# REAP_MARKER_v1
def _reap_stale_in_progress(verbose: bool = True) -> dict:
    """Revert any IN_PROGRESS missions to PENDING when no live daemon owns them.
    Writes a signed ledger entry per reverted mission. Returns {reaped, daemon_alive}.
    """
    result = {"reaped": [], "daemon_alive": False}

    # Check daemon liveness — if alive, refuse to reap (would be unsafe)
    if DAEMON_PID_FILE.exists():
        try:
            pid = int(DAEMON_PID_FILE.read_text().strip())
            os.kill(pid, 0)
            result["daemon_alive"] = True
            if verbose:
                print(c(f"  ⚠️  Daemon alive at PID {pid} — refusing to reap.", C_YELLOW))
                print(c("     Stop the daemon first, then re-run --reap.", C_DIM))
            return result
        except (ProcessLookupError, ValueError, PermissionError):
            pass

    if not MISSION_QUEUE.exists():
        if verbose:
            print(c("  ℹ️  No mission queue — nothing to reap.", C_DIM))
        return result

    try:
        queue = json.loads(MISSION_QUEUE.read_text())
    except Exception as e:
        if verbose:
            print(c(f"  ❌ Queue read error: {e}", C_RED))
        return result

    for m in queue.get("missions", []):
        if m.get("status") == "IN_PROGRESS":
            mid = m.get("id", "?")
            m["status"] = "PENDING"
            m["last_revert_at"] = _now_iso()
            m["last_revert_reason"] = "stale_in_progress_no_live_daemon"
            result["reaped"].append(mid)
            if verbose:
                print(c(f"  ♻️  Reaped: {mid}", C_GREEN))

            # Per-mission signed ledger entry
            try:
                _write_ledger_entry({
                    "ts": _now_iso(),
                    "actor": "core_stop_reap",
                    "action": "STALE_IN_PROGRESS_REAPED",
                    "subject": mid,
                    "original_status": "IN_PROGRESS",
                    "new_status": "PENDING",
                    "reason": "Daemon not alive; mission was crash residue.",
                    "result": "SUCCESS",
                })
            except Exception:
                pass

    if result["reaped"]:
        MISSION_QUEUE.write_text(json.dumps(queue, indent=2))
        if verbose:
            print(c(f"  ✅ Reaped {len(result['reaped'])} stale IN_PROGRESS missions", C_GREEN))
    elif verbose:
        print(c("  ℹ️  No stale IN_PROGRESS missions found.", C_DIM))

    return result

def cmd_stop(args):
    """Stop the orchestrator daemon and optionally unload models."""
    print()
    print(c("═" * 68, C_BOLD))
    print(c("  CORE STOP", C_BOLD))
    print(c("═" * 68, C_BOLD))
    print()

    # --reap: clear stale IN_PROGRESS without touching the daemon
    if getattr(args, "reap", False):
        reap = _reap_stale_in_progress(verbose=True)
        print()
        print(c("─" * 68, C_DIM))
        if reap["daemon_alive"]:
            print(c("  ⚠️  REAP REFUSED — daemon alive", C_YELLOW))
            return 1
        print(c(f"  ✅ REAP COMPLETE ({len(reap['reaped'])} missions)", C_GREEN))
        print()
        return 0

    daemon_result = _stop_daemon(verbose=True)

    if getattr(args, "all", False):
        print()
        print(c("  Unloading all Ollama models...", C_DIM))
        unloaded = _unload_all_ollama_models(verbose=True)
        if unloaded:
            try:
                _write_ledger_entry({
                    "ts": _now_iso(),
                    "actor": "core_stop_cli",
                    "action": "OLLAMA_MODELS_UNLOADED",
                    "models": unloaded,
                    "result": "SUCCESS",
                })
            except Exception:
                pass

    print()
    print(c("─" * 68, C_DIM))
    if daemon_result["stopped"] or "not running" in daemon_result["message"]:
        print(c("  ✅ STOP COMPLETE", C_GREEN))
    else:
        print(c(f"  ⚠️  {daemon_result['message']}", C_YELLOW))
    print()

    return 0 if daemon_result["stopped"] or "not running" in daemon_result["message"] else 1


# ─── CLI WIRING (called by core_cli.py) ──────────────────────


# RESUME_MARKER_v1
def cmd_resume(args):
    """Graceful post-crash recovery: reap stale state, optionally restart daemon."""
    print()
    print(c("═" * 68, C_BOLD))
    print(c("  CORE RESUME — Post-Crash Recovery", C_BOLD))
    print(c("═" * 68, C_BOLD))
    print()

    dry_run = getattr(args, "dry_run", False)
    no_restart = getattr(args, "no_restart", False)

    if dry_run:
        print(c("  🔍 DRY RUN — no changes will be made", C_YELLOW))
        print()

    # Step 1: Stale PID file
    stale_pid = None
    if DAEMON_PID_FILE.exists():
        try:
            pid = int(DAEMON_PID_FILE.read_text().strip())
            os.kill(pid, 0)
            print(c(f"  ⚠️  Daemon already alive at PID {pid}", C_YELLOW))
            print(c(f"     Resume aborted. Use 'core stop --daemon' first.", C_DIM))
            return 1
        except (ProcessLookupError, ValueError):
            stale_pid = pid
            print(f"  {c('🧹 STALE', C_YELLOW)}  Found stale PID file (PID {pid} not running)")
            if not dry_run:
                try:
                    DAEMON_PID_FILE.unlink()
                    print(f"          {c('✅ Removed wilderness_daemon.pid', C_GREEN)}")
                except Exception as e:
                    print(f"          {c(f'❌ Could not remove: {e}', C_RED)}")
        except PermissionError:
            print(c(f"  ⚠️  PID {pid} owned by another user — cannot verify", C_YELLOW))
            return 1
    else:
        print(f"  {c('✅ CLEAN', C_GREEN)}  No PID file present")

    # Step 2: Reap stale IN_PROGRESS missions
    reaped = []
    if MISSION_QUEUE.exists():
        try:
            queue = json.loads(MISSION_QUEUE.read_text())
            in_progress = [m for m in queue.get("missions", [])
                           if m.get("status") == "IN_PROGRESS"]

            if in_progress:
                print(f"  {c('🧹 STALE', C_YELLOW)}  Found {len(in_progress)} IN_PROGRESS missions")
                for m in in_progress:
                    mid = m.get("id", "?")
                    print(f"          {c('♻️ ', C_DIM)} {mid}")
                    if not dry_run:
                        m["status"] = "PENDING"
                        m["last_revert_at"] = _now_iso()
                        m["last_revert_reason"] = "core_resume_post_crash_reap"
                        reaped.append(mid)
                        try:
                            _write_ledger_entry({
                                "ts": _now_iso(),
                                "actor": "core_resume",
                                "action": "POST_CRASH_REAPED",
                                "subject": mid,
                                "original_status": "IN_PROGRESS",
                                "new_status": "PENDING",
                                "reason": "Post-crash recovery: daemon was not alive.",
                                "result": "SUCCESS",
                            })
                        except Exception:
                            pass

                if not dry_run and reaped:
                    MISSION_QUEUE.write_text(json.dumps(queue, indent=2))
                    print(f"          {c(f'✅ Reaped {len(reaped)} missions', C_GREEN)}")
            else:
                print(f"  {c('✅ CLEAN', C_GREEN)}  No stale IN_PROGRESS missions")
        except Exception as e:
            print(f"  {c('❌ ERROR', C_RED)}  Queue read failed: {e}")
            return 1

    # Step 3: Check Ollama
    try:
        import urllib.request
        req = urllib.request.Request(f"{OLLAMA_URL}/api/tags")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
            count = len(data.get("models", []))
            print(f"  {c('✅ ALIVE', C_GREEN)}  Ollama reachable, {count} models available")
    except Exception:
        print(f"  {c('⚠️  DOWN', C_YELLOW)}  Ollama not responding")
        print(f"          {c(f'→ Start with: systemctl --user restart ollama', C_DIM)}")
        if not dry_run:
            print(c("\n  Cannot restart daemon while Ollama is down. Resolve and re-run.", C_RED))
            return 1

    # Step 4: Restart daemon
    if no_restart:
        print()
        print(c("  ℹ️  --no-restart: daemon NOT restarted", C_CYAN))
    elif dry_run:
        print()
        print(c("  🔍 Would restart daemon (skipped: dry-run)", C_YELLOW))
    else:
        print()
        print(c("  Restarting daemon...", C_DIM))
        log_file = REPO_ROOT / "wilderness_run.log"
        orchestrator = SCRIPTS / "orchestrator_loop.py"

        if not orchestrator.exists():
            print(f"  {c('❌ FAIL', C_RED)}  Orchestrator script not found at {orchestrator}")
            return 1

        try:
            with open(log_file, "ab") as logf:
                logf.write(f"\n=== core resume restart {_now_iso()} ===\n".encode())
                proc = subprocess.Popen(
                    [sys.executable, str(orchestrator), "--daemon", "--interval", "60"],
                    stdout=logf, stderr=subprocess.STDOUT,
                    cwd=str(REPO_ROOT),
                    start_new_session=True,
                )
            DAEMON_PID_FILE.write_text(str(proc.pid))
            time.sleep(2)
            try:
                os.kill(proc.pid, 0)
                print(f"  {c('✅ STARTED', C_GREEN)}  Daemon running at PID {proc.pid}")
                _write_ledger_entry({
                    "ts": _now_iso(),
                    "actor": "core_resume",
                    "action": "DAEMON_RESTARTED_POST_CRASH",
                    "pid": proc.pid,
                    "reaped_missions": reaped,
                    "stale_pid_removed": stale_pid,
                    "result": "SUCCESS",
                })
            except ProcessLookupError:
                print(f"  {c('❌ FAIL', C_RED)}  Daemon died immediately after start")
                return 1
        except Exception as e:
            print(f"  {c('❌ FAIL', C_RED)}  Could not start daemon: {e}")
            return 1

    print()
    print(c("─" * 68, C_DIM))
    print(c("  ✅ RESUME COMPLETE", C_GREEN))
    print()
    return 0

def register_subparsers(sub) -> None:
    """Register the 'doctor' and 'stop' subcommands. Called by core_cli.py."""
    # Doctor: no args
    sub.add_parser("doctor", help="Run system diagnostics")

    # Resume: post-crash recovery
    resume_parser = sub.add_parser("resume", help="Recover from a hard reset / crash")
    resume_parser.add_argument("--dry-run", action="store_true",
                                help="Show what would happen without making changes")
    resume_parser.add_argument("--no-restart", action="store_true",
                                help="Reap stale state but don't restart daemon")

    # Stop: --daemon (default) or --all
    stop_parser = sub.add_parser("stop", help="Stop daemon and/or unload models")
    stop_parser.add_argument("--daemon", action="store_true",
                             help="Stop the orchestrator daemon (default)")
    stop_parser.add_argument("--all", action="store_true",
                             help="Stop daemon AND unload all Ollama models")
    stop_parser.add_argument("--reap", action="store_true",
                             help="Reap stale IN_PROGRESS missions only (no daemon stop)")


# Map for COMMANDS dict in core_cli.py
COMMAND_HANDLERS = {
    "doctor": cmd_doctor,
    "stop": cmd_stop,
    "resume": cmd_resume,
}


if __name__ == "__main__":
    # Standalone test
    parser = argparse.ArgumentParser(prog="core-extensions")
    sub = parser.add_subparsers(dest="command")
    register_subparsers(sub)
    args = parser.parse_args()

    if args.command == "doctor":
        sys.exit(cmd_doctor(args))
    elif args.command == "stop":
        sys.exit(cmd_stop(args))
    else:
        parser.print_help()


# ═════════════════════════════════════════════════════════════
# WIRING INSTRUCTIONS for scripts/core_cli.py
# ═════════════════════════════════════════════════════════════
#
# 1. Add to imports near the top:
#       from core_cli_extensions import (
#           register_subparsers as _register_extensions,
#           COMMAND_HANDLERS as _EXTENSION_HANDLERS,
#       )
#
# 2. In build_parser(), after all existing sub.add_parser calls and
#    before `return parser`, add:
#       _register_extensions(sub)
#
# 3. In the COMMANDS dict, after the existing entries, add:
#       **_EXTENSION_HANDLERS,
#
# 4. Update cmd_help() to include the new commands in the help text:
#       core doctor                 Run system diagnostics
#       core stop --daemon          Stop the orchestrator daemon
#       core stop --all             Stop daemon + unload all models
#
# A patch script (patch_core_cli_extensions.py) automates these edits.
# ═════════════════════════════════════════════════════════════
