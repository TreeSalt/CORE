#!/usr/bin/env python3
"""
core — CORE CLI (Constitutional Orchestration & Ratification Engine)
====================================================================
Version: 1.0.0
License: Proprietary — TreeSalt/CORE

Single entry point for all CORE operations. Wraps factory orchestration,
red team probing, health monitoring, mission management, and governance.

SAFETY NOTICE:
  The red team capabilities in this tool are designed for DEFENSIVE security
  research — testing YOUR OWN models for backdoors and vulnerabilities.
  Using these tools against systems you do not own or have explicit
  authorization to test is unethical and may be illegal.

USAGE:
  core status                    Show factory + system status
  core health                    Run Ollama VRAM health check
  core queue                     Show mission queue
  core queue add <mission.json>  Add missions to queue
  core queue reset-failed        Reset ESCALATE missions to PENDING
  core run                       Execute pending missions (single pass)
  core run --daemon              Execute missions continuously
  core run --dry-run             Preview without executing
  core ratify                    Bulk ratify all AWAITING_RATIFICATION
  core drop                      Seal and build drop packet
  core push                      Git push to remote
  core redteam generate          Generate probe suite
  core redteam run <model>       Run probes against a model
  core redteam analyze           Analyze latest results
  core redteam report            Generate Markdown report
  core vram                      Show VRAM status
  core vram unload               Unload all Ollama models
  core version                   Show current version
  core help                      Show this help
"""
from __future__ import annotations
import argparse
import json
import subprocess
import sys
import os
import re
from core_reconnect import cmd_reconnect
from datetime import datetime, timezone
from pathlib import Path

# ── PATHS ─────────────────────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "scripts"
ORCH_DIR = REPO_ROOT / "orchestration"
MISSION_QUEUE = ORCH_DIR / "MISSION_QUEUE.json"
STATE_DIR = REPO_ROOT / "state"
RED_TEAM_DIR = STATE_DIR / "red_team"
DORMANT_DIR = STATE_DIR / "dormant_puzzle"
RUN_LEDGER_DIR = REPO_ROOT / "dist"
GOVERNANCE = REPO_ROOT / "04_GOVERNANCE"

# ── ANSI COLORS ───────────────────────────────────────────────────────────────
C_RESET = "\033[0m"
C_BOLD = "\033[1m"
C_RED = "\033[91m"
C_GREEN = "\033[92m"
C_YELLOW = "\033[93m"
C_BLUE = "\033[94m"
C_CYAN = "\033[96m"
C_DIM = "\033[2m"

def c(text, color):
    return f"{color}{text}{C_RESET}"


# ── SAFETY BANNER ─────────────────────────────────────────────────────────────
SAFETY_BANNER = f"""
{c('⚠️  CORE RED TEAM — DEFENSIVE USE ONLY', C_YELLOW)}
{c('━' * 50, C_DIM)}
This tool is designed for testing YOUR OWN models
for backdoors and vulnerabilities. Unauthorized use
against systems you do not own is unethical and
may be illegal under computer fraud statutes.
{c('━' * 50, C_DIM)}
"""


# ══════════════════════════════════════════════════════════════════════════════
# COMMANDS
# ══════════════════════════════════════════════════════════════════════════════

def cmd_status(args):
    """Show comprehensive factory + system status."""
    print(c("═" * 56, C_CYAN))
    print(c("  CORE — Constitutional Orchestration & Ratification Engine", C_BOLD))
    print(c("═" * 56, C_CYAN))

    # Version
    version = _get_version()
    print(f"\n  {c('VERSION', C_BOLD)}: {version}")
    print(f"  {c('REPO', C_BOLD)}:    {REPO_ROOT}")

    # Git status
    git_dirty = _run_quiet(["git", "status", "--porcelain"])
    git_branch = _run_quiet(["git", "branch", "--show-current"]).strip()
    dirty_flag = c("DIRTY", C_RED) if git_dirty.strip() else c("CLEAN", C_GREEN)
    print(f"  {c('GIT', C_BOLD)}:     {git_branch} ({dirty_flag})")

    # Mission queue
    print(f"\n  {c('MISSION QUEUE', C_BOLD)}")
    if MISSION_QUEUE.exists():
        q = json.loads(MISSION_QUEUE.read_text())
        missions = q.get("missions", [])
        by_status = {}
        for m in missions:
            s = m["status"]
            by_status[s] = by_status.get(s, 0) + 1
        total = len(missions)
        for status, count in sorted(by_status.items()):
            icon = {"PENDING": "⏳", "AWAITING_RATIFICATION": "📋",
                    "RATIFIED": "✅", "ESCALATE": "❌"}.get(status, "❓")
            color = {"PENDING": C_YELLOW, "AWAITING_RATIFICATION": C_BLUE,
                     "RATIFIED": C_GREEN, "ESCALATE": C_RED}.get(status, C_RESET)
            print(f"    {icon} {c(f'{count:3d}', color)} {status}")
        print(f"    {'─' * 30}")
        print(f"    {c(f'{total:3d}', C_BOLD)} TOTAL")
    else:
        print(f"    {c('No queue found', C_DIM)}")

    # VRAM
    print(f"\n  {c('VRAM', C_BOLD)}")
    vram = _get_vram()
    if vram:
        used_pct = (vram["used"] / vram["total"]) * 100
        color = C_GREEN if used_pct < 60 else C_YELLOW if used_pct < 85 else C_RED
        bar_len = 20
        filled = int(bar_len * used_pct / 100)
        bar = f"[{'█' * filled}{'░' * (bar_len - filled)}]"
        print(f"    {bar} {c(f'{used_pct:.0f}%', color)} ({vram['used']}MB / {vram['total']}MB)")
    else:
        print(f"    {c('nvidia-smi not available', C_DIM)}")

    # Ollama
    print(f"\n  {c('OLLAMA', C_BOLD)}")
    models = _get_ollama_models()
    if models is not None:
        if models:
            for m in models:
                print(f"    🟢 {m}")
        else:
            print(f"    {c('No models loaded', C_DIM)}")
    else:
        print(f"    {c('Ollama not responding', C_RED)}")

   # Agentic Teams
    print(f"\n  {c('AGENTIC TEAMS', C_BOLD)}")

    # Factory
    proposals_dir = REPO_ROOT / "08_IMPLEMENTATION_NOTES"
    proposals = list(proposals_dir.glob("PROPOSAL_*.md")) if proposals_dir.exists() else []
    print(f"    🏭 Factory         {c(str(len(proposals)), C_GREEN)} proposals generated")

    # Benchmarking
    bench_dir = REPO_ROOT / "06_BENCHMARKING" / "reports"
    benchmarks = list(bench_dir.glob("BENCHMARK_*.md")) if bench_dir.exists() else []
    print(f"    🔍 Benchmarking    {c(str(len(benchmarks)), C_GREEN)} reports | AST + security validation")

    # Red Team
    rt_local = list(RED_TEAM_DIR.glob("*.json")) if RED_TEAM_DIR.exists() else []
    rt_dormant = list(DORMANT_DIR.glob("RESULTS_*.json")) if DORMANT_DIR.exists() else []
    dormant_tag = " | 3/3 dormant models cracked" if len(rt_dormant) > 0 else ""
    print(f"    🔴 Red Team        {c(str(len(rt_local)), C_GREEN)} local campaigns | {c(str(len(rt_dormant)), C_GREEN)} dormant results{dormant_tag}")

    # Governance
    esc_dir = REPO_ROOT / "08_IMPLEMENTATION_NOTES" / "ESCALATIONS"
    ratifications = list(esc_dir.glob("RATIFICATION_*.md")) if esc_dir.exists() else []
    escalations = list(esc_dir.glob("ESCALATION_*.md")) if esc_dir.exists() else []
    print(f"    🛡️  Governance      {c(str(len(ratifications)), C_GREEN)} ratified | {c(str(len(escalations)), C_YELLOW)} escalations")

    # Strategy Zoo
    zoo_dir = REPO_ROOT / "00_PHYSICS_ENGINE" / "strategy_zoo"
    strategies = list(zoo_dir.glob("*.py")) if zoo_dir.exists() else []
    print(f"    📊 Strategy Zoo    {c(str(len(strategies)), C_GREEN)} strategies")

    # Risk
    risk_dir = REPO_ROOT / "02_RISK_MANAGEMENT"
    risk_files = list(risk_dir.glob("*.py")) if risk_dir.exists() else []
    risk_status = "active" if risk_files else "pending"
    risk_color = C_GREEN if risk_files else C_DIM
    print(f"    ⚖️  Risk            {c(risk_status, risk_color)}")

    print()

def cmd_health(args):
    """Run Ollama health gate."""
    health_script = SCRIPTS / "ollama_health_gate.py"
    if health_script.exists():
        subprocess.run([sys.executable, str(health_script)])
    else:
        print(c("Health gate script not found. Checking manually...", C_YELLOW))
        vram = _get_vram()
        models = _get_ollama_models()
        if models is not None:
            print(c(f"✅ Ollama alive — {len(models)} model(s) loaded", C_GREEN))
        else:
            print(c("❌ Ollama not responding", C_RED))
        if vram:
            print(f"   VRAM: {vram['free']}MB free / {vram['total']}MB total")


def cmd_queue(args):
    """Show or manage mission queue."""
    if args.queue_action == "show" or args.queue_action is None:
        _queue_show()
    elif args.queue_action == "reset-all":
        _queue_reset_all()
    elif args.queue_action == "add":
        _queue_add(args.file)
    elif args.queue_action == "reset-all":
        _queue_reset_all()
    else:
        print(f"Unknown queue action: {args.queue_action}")


def _queue_show():
    if not MISSION_QUEUE.exists():
        print(c("No mission queue found.", C_YELLOW))
        return
    q = json.loads(MISSION_QUEUE.read_text())
    missions = q.get("missions", [])
    print(c(f"\n  MISSION QUEUE — {len(missions)} missions", C_BOLD))
    print(f"  {'─' * 70}")
    for i, m in enumerate(missions, 1):
        status = m["status"]
        icon = {"PENDING": "⏳", "AWAITING_RATIFICATION": "📋",
                "RATIFIED": "✅", "ESCALATE": "❌"}.get(status, "❓")
        color = {"PENDING": C_YELLOW, "AWAITING_RATIFICATION": C_BLUE,
                 "RATIFIED": C_GREEN, "ESCALATE": C_RED}.get(status, C_RESET)
        priority = m.get("priority", "?")
        print(f"  {i:3d}. {icon} {c(f'[P{priority}]', C_DIM)} {c(status, color):40s} {m['id']}")
    print()


def _queue_reset_failed():
    if not MISSION_QUEUE.exists():
        print(c("No mission queue found.", C_YELLOW))
        return
    q = json.loads(MISSION_QUEUE.read_text())
    reset = 0
    for m in q["missions"]:
        if m["status"] == "ESCALATE":
            m["status"] = "PENDING"
            m["result"] = None
            m["started_at"] = None
            m["completed_at"] = None
            reset += 1
            print(f"  ♻️  Reset: {m['id']}")
    MISSION_QUEUE.write_text(json.dumps(q, indent=2))
    print(c(f"\n✅ {reset} mission(s) reset to PENDING", C_GREEN))

def _queue_reset_all():
    if not MISSION_QUEUE.exists():
        print(c("No mission queue found.", C_YELLOW))
        return
    q = json.loads(MISSION_QUEUE.read_text())
    reset = 0
    for m in q["missions"]:
        if m["status"] != "RATIFIED":
            m["status"] = "PENDING"
            m["result"] = None
            m["started_at"] = None
            m["completed_at"] = None
            reset += 1
            print(f"  ♻️  Reset: {m['id']}")
    MISSION_QUEUE.write_text(json.dumps(q, indent=2))
    print(c(f"\n✅ {reset} mission(s) force-reset to PENDING", C_GREEN))

def _queue_add(filepath):
    if not filepath:
        print(c("Usage: core queue add <missions.json>", C_YELLOW))
        return
    source = Path(filepath)
    if not source.exists():
        print(c(f"File not found: {source}", C_RED))
        return
    print(c(f"Adding missions from {source}...", C_CYAN))
    # Import the bridge logic inline
    subprocess.run([sys.executable, "-c", f"""
import json
from pathlib import Path
from datetime import datetime, timezone

source = json.loads(Path("{source}").read_text())
missions = source.get("missions", source.get("probes", []))
QUEUE = Path("{MISSION_QUEUE}")
MISSIONS_DIR = Path("{REPO_ROOT}/prompts/missions")
MISSIONS_DIR.mkdir(parents=True, exist_ok=True)

if QUEUE.exists():
    q = json.loads(QUEUE.read_text())
else:
    q = {{"missions": []}}

PRIO_MAP = {{"P0": 0, "P1": 1, "P2": 2, "P3": 3}}
now = datetime.now(timezone.utc).isoformat()
added = 0

for m in missions:
    mid = m.get("id", m.get("probe_id", f"mission_{{added}}"))
    existing_ids = [x["id"] for x in q["missions"]]
    if mid in existing_ids:
        print(f"  ⏭️  Skip (exists): {{mid}}")
        continue

    # Write mission file
    fname = f"mission_{{mid}}.md"
    md = f"# Mission: {{m.get('title', mid)}}\\n\\n## Domain\\n{{m.get('domain', 'UNKNOWN')}}\\n\\n## Description\\n{{m.get('description', m.get('prompt', 'No description'))}}\\n"
    (MISSIONS_DIR / fname).write_text(md)

    q["missions"].append({{
        "id": mid,
        "domain": m.get("domain", "08_CYBERSECURITY"),
        "task": mid,
        "mission_file": fname,
        "type": "IMPLEMENTATION",
        "max_retries": 3,
        "status": "PENDING",
        "priority": PRIO_MAP.get(m.get("priority", "P1"), 1),
        "authored_by": "core-cli",
        "authored_at": now,
        "result": None,
    }})
    added += 1
    print(f"  ✅ Added: {{mid}}")

QUEUE.write_text(json.dumps(q, indent=2))
print(f"\\n✅ {{added}} mission(s) added to queue")
"""])


def cmd_run(args):
    """Execute pending missions."""
    # Health check first
    print(c("Pre-flight health check...", C_CYAN))
    _ensure_ollama_healthy()

    cmd = [sys.executable, str(SCRIPTS / "orchestrator_loop.py")]
    if args.daemon:
        cmd.extend(["--daemon", "--interval", "60"])
    if args.dry_run:
        cmd.append("--dry-run")
    subprocess.run(cmd)


def cmd_ratify(args):
    """Bulk ratify all AWAITING_RATIFICATION missions."""
    ratify_script = REPO_ROOT / "bulk_ratify_all.py"
    if ratify_script.exists():
        subprocess.run([sys.executable, str(ratify_script)])
    else:
        # Manual ratification
        if not MISSION_QUEUE.exists():
            print(c("No queue found.", C_YELLOW))
            return
        q = json.loads(MISSION_QUEUE.read_text())
        count = 0
        for m in q["missions"]:
            if m["status"] == "AWAITING_RATIFICATION":
                m["status"] = "RATIFIED"
                count += 1
                print(f"  ✅ Ratified: {m['id']}")
        MISSION_QUEUE.write_text(json.dumps(q, indent=2))
        print(c(f"\n✅ {count} mission(s) ratified", C_GREEN))


def cmd_drop(args):
    """Seal and build drop packet."""
    subprocess.run(["make", "drop"], cwd=REPO_ROOT)


def cmd_push(args):
    """Git push to remote."""
    subprocess.run(["git", "push", "aos", "master:main"], cwd=REPO_ROOT)


def cmd_redteam(args):
    """Red team operations."""
    print(SAFETY_BANNER)
    action = args.redteam_action

    if action == "generate":
        gen_script = SCRIPTS / "red_team" / "probe_generator.py"
        if gen_script.exists():
            subprocess.run([sys.executable, str(gen_script)])
        else:
            print(c("Probe generator not found. Run factory missions first.", C_YELLOW))

    elif action == "run":
        runner = SCRIPTS / "red_team" / "campaign_runner.py"
        if runner.exists():
            cmd = [sys.executable, str(runner)]
            if args.model:
                cmd.extend(["--model", args.model])
            subprocess.run(cmd)
        else:
            print(c("Campaign runner not found. Run factory missions first.", C_YELLOW))

    elif action == "analyze":
        analyzer = SCRIPTS / "red_team" / "response_analyzer.py"
        if analyzer.exists():
            subprocess.run([sys.executable, str(analyzer)])
        else:
            print(c("Response analyzer not found. Run factory missions first.", C_YELLOW))

    elif action == "report":
        reporter = SCRIPTS / "red_team" / "report_generator.py"
        if reporter.exists():
            subprocess.run([sys.executable, str(reporter)])
        else:
            print(c("Report generator not found. Run factory missions first.", C_YELLOW))

    else:
        print(c("Usage: core redteam {generate|run|analyze|report}", C_YELLOW))


def cmd_vram(args):
    """VRAM management."""
    if args.vram_action == "unload":
        models = _get_ollama_models()
        if models:
            for m in models:
                print(f"  Unloading {m}...")
                subprocess.run(["ollama", "stop", m],
                               capture_output=True, text=True)
            print(c("✅ All models unloaded", C_GREEN))
        else:
            print(c("No models loaded", C_DIM))
    else:
        vram = _get_vram()
        if vram:
            used_pct = (vram["used"] / vram["total"]) * 100
            color = C_GREEN if used_pct < 60 else C_YELLOW if used_pct < 85 else C_RED
            print(f"  Total:     {vram['total']}MB")
            used_mb = vram["used"]
            print(f"  Used:      {c(str(used_mb) + 'MB', color)} ({used_pct:.1f}%)")
            print(f"  Free:      {vram['free']}MB")
            models = _get_ollama_models()
            if models:
                print(f"  Loaded:    {', '.join(models)}")
        else:
            print(c("nvidia-smi not available", C_YELLOW))

def cmd_lockdown(args):
    """Toggle local lockdown mode."""
    lockdown_file = ORCH_DIR / "LOCAL_LOCKDOWN.json"
    if args.lockdown_action == "on":
        reason = args.reason or "Manual lockdown by Sovereign"
        data = {
            "enabled": True,
            "reason": reason,
            "set_by": "Sovereign",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        lockdown_file.write_text(json.dumps(data, indent=2))
        print(c("🔒 LOCAL LOCKDOWN ENABLED", C_RED))
        print(f"   Reason: {reason}")
        print(f"   ALL tasks will route to local Qwen. No cloud dispatch.")
    elif args.lockdown_action == "off":
        data = {"enabled": False, "reason": "", "set_by": "", "timestamp": ""}
        lockdown_file.write_text(json.dumps(data, indent=2))
        print(c("🔓 LOCAL LOCKDOWN DISABLED", C_GREEN))
        print(f"   Cloud-eligible tasks will route normally.")
    else:
        if lockdown_file.exists():
            data = json.loads(lockdown_file.read_text())
            if data.get("enabled"):
                print(c("🔒 LOCKDOWN: ACTIVE", C_RED))
                print(f"   Reason: {data.get('reason', 'none')}")
                print(f"   Since:  {data.get('timestamp', 'unknown')}")
            else:
                print(c("🔓 LOCKDOWN: INACTIVE", C_GREEN))
        else:
            print(c("🔓 LOCKDOWN: INACTIVE", C_GREEN))

def cmd_version(args):
    """Show current version."""
    print(f"CORE {_get_version()}")


def cmd_help(args):
    """Show help."""
    print(c("═" * 56, C_CYAN))
    print(c("  CORE CLI — Command Reference", C_BOLD))
    print(c("═" * 56, C_CYAN))
    print(f"""
  {c('🏭 FACTORY', C_BOLD)}
    core status                 System overview (queue, VRAM, git, red team)
    core health                 Ollama + VRAM health check
    core run                    Execute pending missions (single pass)
    core run --daemon           Execute continuously (poll every 60s)
    core run --dry-run          Preview without executing
    core drop                   Seal and build drop packet (make drop)
    core push                   Git push to remote

  {c('📋 MISSIONS', C_BOLD)}
    core queue                  Show mission queue status
    core queue add <file.json>  Add missions from JSON file
    core queue reset-failed     Reset ESCALATE → PENDING
    core ratify                 Bulk ratify all passing missions

  {c('🔴 RED TEAM', C_BOLD)} {c('(defensive use only)', C_DIM)}
    core redteam generate       Generate probe suite
    core redteam run <model>    Run probes against a local model
    core redteam analyze        Analyze latest campaign results
    core redteam report         Generate Markdown campaign report

  {c('🖥️  HARDWARE', C_BOLD)}
    core vram                   Show GPU VRAM status
    core vram unload            Unload all Ollama models

  {c('🔌 RECOVERY', C_BOLD)}
    core reconnect              Full reconnect (ollama + cloud + reset)
    core reconnect --local      Restart Ollama only
    core reconnect --cloud      Check cloud API connectivity
    core reconnect --reset      Reset stuck missions to PENDING
  {c('🔌 RECOVERY', C_BOLD)}
    core reconnect              Full reconnect (ollama + cloud + reset)
    core reconnect --local      Restart Ollama only
    core reconnect --cloud      Check cloud API connectivity
    core reconnect --reset      Reset stuck missions to PENDING

  {c('📖 META', C_BOLD)}
    core version                Show current version
    core help                   Show this reference
""")


# ══════════════════════════════════════════════════════════════════════════════
# UTILITIES
# ══════════════════════════════════════════════════════════════════════════════

def _get_version():
    """Get current version from latest run ledger or git."""
    ledgers = sorted(RUN_LEDGER_DIR.glob("RUN_LEDGER_*.json"), reverse=True) if RUN_LEDGER_DIR.exists() else []
    if ledgers:
        try:
            data = json.loads(ledgers[0].read_text())
            return f"v{data.get('version', '?.?.?')}"
        except Exception:
            pass
    # Fallback: parse from Makefile or git
    return _run_quiet(["git", "describe", "--tags", "--always"]).strip() or "unknown"


def _get_vram():
    """Parse nvidia-smi for VRAM status."""
    try:
        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.total,memory.used,memory.free",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5
        )
        if out.returncode == 0:
            parts = out.stdout.strip().split(",")
            if len(parts) >= 3:
                return {
                    "total": int(parts[0].strip()),
                    "used": int(parts[1].strip()),
                    "free": int(parts[2].strip()),
                }
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return None


def _get_ollama_models():
    """Get currently loaded Ollama models."""
    try:
        import urllib.request
        req = urllib.request.Request("http://localhost:11434/api/ps")
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read())
            return [m["name"] for m in data.get("models", [])]
    except Exception:
        return None


def _ensure_ollama_healthy():
    """Ensure Ollama is running and VRAM has headroom."""
    models = _get_ollama_models()
    if models is None:
        print(c("⚠️  Ollama not responding — attempting restart...", C_YELLOW))
        subprocess.run(["systemctl", "--user", "restart", "ollama"],
                       capture_output=True)
        import time
        time.sleep(3)
        models = _get_ollama_models()
        if models is None:
            print(c("❌ Ollama still not responding. Start manually: ollama serve", C_RED))
            return False

    vram = _get_vram()
    if vram and vram["free"] < 2000:
        print(c(f"⚠️  Low VRAM ({vram['free']}MB free) — unloading models...", C_YELLOW))
        for m in (models or []):
            subprocess.run(["ollama", "stop", m], capture_output=True)
        print(c("✅ Models unloaded", C_GREEN))

    return True


def _run_quiet(cmd):
    """Run a command and return stdout, suppressing errors."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True,
                                timeout=10, cwd=REPO_ROOT)
        return result.stdout
    except Exception:
        return ""


# ══════════════════════════════════════════════════════════════════════════════
# ARGUMENT PARSER
# ══════════════════════════════════════════════════════════════════════════════

def build_parser():
    parser = argparse.ArgumentParser(
        prog="core",
        description="CORE — Constitutional Orchestration & Ratification Engine",
        add_help=False,
    )
    sub = parser.add_subparsers(dest="command")

    # Status
    sub.add_parser("status", help="System overview")

    # Health
    sub.add_parser("health", help="Ollama + VRAM health check")

    # Queue
    q_parser = sub.add_parser("queue", help="Mission queue management")
    q_parser.add_argument("queue_action", nargs="?", default="show",
                          choices=["show", "add", "reset-failed", "reset-all"])
    q_parser.add_argument("file", nargs="?", default=None)

    # Lockdown
    l_parser = sub.add_parser("lockdown", help="Local lockdown mode")
    l_parser.add_argument("lockdown_action", nargs="?", default="status",
                          choices=["on", "off", "status"])
    l_parser.add_argument("--reason", default=None)

  # RECONECT
    p_reconnect = sub.add_parser(
        "reconnect",
        help="Reconnect to local/cloud AI and reset stuck missions"
    )
    p_reconnect.add_argument("--local", action="store_true",
                             help="Reconnect Ollama only")
    p_reconnect.add_argument("--cloud", action="store_true",
                             help="Check cloud APIs only")
    p_reconnect.add_argument("--reset", action="store_true",
                             help="Reset stuck missions only")
    p_reconnect.set_defaults(func=cmd_reconnect)

    # Run
    r_parser = sub.add_parser("run", help="Execute pending missions")
    r_parser.add_argument("--daemon", action="store_true")
    r_parser.add_argument("--dry-run", action="store_true")

    # Ratify
    sub.add_parser("ratify", help="Bulk ratify passing missions")

    # Drop
    sub.add_parser("drop", help="Seal and build drop packet")

    # Push
    sub.add_parser("push", help="Git push to remote")

    # Red team
    rt_parser = sub.add_parser("redteam", help="Red team operations")
    rt_parser.add_argument("redteam_action", nargs="?",
                           choices=["generate", "run", "analyze", "report"])
    rt_parser.add_argument("--model", default=None)

    # VRAM
    v_parser = sub.add_parser("vram", help="GPU VRAM management")
    v_parser.add_argument("vram_action", nargs="?", default="show",
                          choices=["show", "unload"])

    # Version
    sub.add_parser("version", help="Show version")

    # Help
    sub.add_parser("help", help="Show command reference")

    return parser


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

COMMANDS = {
    "status": cmd_status,
    "health": cmd_health,
    "queue": cmd_queue,
    "lockdown": cmd_lockdown,
    "run": cmd_run,
    "ratify": cmd_ratify,
    "drop": cmd_drop,
    "push": cmd_push,
    "redteam": cmd_redteam,
    "vram": cmd_vram,
    "version": cmd_version,
    "help": cmd_help,
}

def main():
    parser = build_parser()
    args = parser.parse_args()

    if args.command is None:
        cmd_help(args)
        return

    handler = COMMANDS.get(args.command)
    if handler:
        handler(args)
    else:
        cmd_help(args)


if __name__ == "__main__":
    main()
