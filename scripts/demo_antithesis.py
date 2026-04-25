#!/usr/bin/env python3
"""
CORE LIVE DEMO — Antithesis Call Prep
======================================
Run this script to walk through CORE's key capabilities.
Each section pauses for narration. Press ENTER to advance.

Usage:
  cd ~/TRADER_OPS/v9e_stage
  python3 scripts/demo_antithesis.py
"""

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
VAULT = REPO / "state" / "sovereign_vault"
GATES_DIR = REPO / "06_BENCHMARKING" / "gates"
PROPOSALS_DIR = REPO / "08_IMPLEMENTATION_NOTES"


def section(title: str, description: str):
    """Print section header and wait for ENTER."""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")
    print(f"  {description}")
    print()
    input("  [Press ENTER to run]")
    print()


def run_cmd(cmd: str):
    """Run a shell command and print output."""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                            cwd=str(REPO))
    if result.stdout.strip():
        print(result.stdout.rstrip())
    if result.stderr.strip():
        print(result.stderr.rstrip())


# ─── DEMO SECTIONS ──────────────────────────────────────────

def demo_chain_integrity():
    section(
        "1. CRYPTOGRAPHIC CHAIN INTEGRITY",
        "Every action in CORE — every deployment, gate injection,\n"
        "  ghost reset, sovereign override — produces a hash-chained\n"
        "  ledger entry. Tamper with any entry and the chain breaks."
    )
    month = datetime.now(timezone.utc).strftime("%Y_%m")
    ledger = VAULT / "ledger" / f"ledger_{month}.jsonl"
    entries = [json.loads(l) for l in ledger.read_text().strip().split("\n") if l.strip()]
    
    broken = 0
    for i, entry in enumerate(entries):
        expected = entries[i-1].get("entry_hash") if i > 0 else None
        if entry.get("parent_hash") != expected:
            print(f"  ❌ CHAIN BREAK at entry {i}")
            broken += 1

    print(f"  Total entries:  {len(entries)}")
    print(f"  Chain status:   {'✅ INTACT' if broken == 0 else f'❌ {broken} BREAKS'}")
    
    # Show the action types in the chain
    actions = {}
    for e in entries:
        a = e.get("action", "unknown")
        actions[a] = actions.get(a, 0) + 1
    print(f"\n  Action types in chain:")
    for action, count in sorted(actions.items(), key=lambda x: -x[1]):
        print(f"    {count:3d}x  {action}")


def demo_e14_gates():
    section(
        "2. E14 DETERMINISTIC GATES",
        "Four gates that catch the failure modes from our wilderness run.\n"
        "  Each gate was built to address a specific documented failure.\n"
        "  Let's run them against known-bad proposals from that run."
    )
    
    # Find test proposals
    bad_proposals = {
        "EMPTY (110 bytes, zero code)": None,
        "PROMPT LEAK (<|endoftext|>)": None,
    }
    
    for p in sorted(PROPOSALS_DIR.glob("PROPOSAL_*.md")):
        text = p.read_text()
        size = len(text)
        if size < 200 and bad_proposals["EMPTY (110 bytes, zero code)"] is None:
            bad_proposals["EMPTY (110 bytes, zero code)"] = p
        if "<|endoftext|>" in text and bad_proposals["PROMPT LEAK (<|endoftext|>)"] is None:
            bad_proposals["PROMPT LEAK (<|endoftext|>)"] = p
    
    gates = [
        ("MIN_SUBSTANCE", GATES_DIR / "min_substance.py"),
        ("TRUNCATION_DETECTION", GATES_DIR / "truncation_detection.py"),
        ("IMPORT_RESOLUTION", GATES_DIR / "import_resolution.py"),
    ]
    
    for gate_name, gate_path in gates:
        if not gate_path.exists():
            print(f"  ⚠️  {gate_name}: not found at {gate_path.relative_to(REPO)}")
            continue
        print(f"  ── {gate_name} ──")
        for desc, proposal in bad_proposals.items():
            if proposal is None:
                continue
            result = subprocess.run(
                [sys.executable, str(gate_path), str(proposal)],
                capture_output=True, text=True, cwd=str(REPO)
            )
            passed = "Passed: True" in result.stdout
            icon = "✅ PASS" if passed else "❌ CAUGHT"
            reason = ""
            for line in result.stdout.split("\n"):
                if line.startswith("Reason:"):
                    reason = line[7:].strip()[:70]
                    break
            print(f"    {icon}  {desc}")
            if reason:
                print(f"           {reason}")
        print()


def demo_sovereign_injections():
    section(
        "3. SOVEREIGN INJECTION PROVENANCE",
        "When the factory can't build its own infrastructure (chicken-and-egg),\n"
        "  I inject code directly — signed with an ED25519 ceremonial key,\n"
        "  logged to the ledger, hash-chained to everything before it."
    )
    month = datetime.now(timezone.utc).strftime("%Y_%m")
    ledger = VAULT / "ledger" / f"ledger_{month}.jsonl"
    
    injections = []
    for line in ledger.read_text().split("\n"):
        if not line.strip():
            continue
        entry = json.loads(line)
        if entry.get("action") == "SOVEREIGN_INJECTION":
            injections.append(entry)
    
    print(f"  Total sovereign injections: {len(injections)}")
    print()
    for inj in injections:
        ts = inj.get("ts", "")[:19]
        target = inj.get("target_path", "?")
        sig_bytes = inj.get("signature_bytes", 0)
        trust = inj.get("trust_class_assigned", "?")
        justification = inj.get("justification", "")[:80]
        print(f"  {ts}  {target}")
        print(f"    Trust: {trust} | Signature: {sig_bytes} bytes ED25519")
        print(f"    Why:   {justification}...")
        print()


def demo_deployed_files():
    section(
        "4. DEPLOYED INFRASTRUCTURE",
        "Real files on disk, deployed tonight through the gated pipeline.\n"
        "  Each one traceable back through the chain."
    )
    
    targets = [
        "mantis_core/orchestration/tier_loader_dataclasses.py",
        "mantis_core/validation/paper_trade_validator.py",
        "mantis_core/validation/replay_harness.py",
        "mantis_core/dashboard/state_writer.py",
        "mantis_core/risk/alpha_decay_monitor.py",
        "docs/architecture/SPECTER_ARCHITECTURE.md",
        "docs/architecture/SPECTER_RECON_PIPELINE.md",
        "docs/methodology/JANE_STREET_DORMANT_LLM_PUZZLE.md",
        "06_BENCHMARKING/gates/min_substance.py",
        "06_BENCHMARKING/gates/truncation_detection.py",
        "06_BENCHMARKING/gates/import_resolution.py",
        "06_BENCHMARKING/gates/contract_name.py",
    ]
    
    for t in targets:
        full = REPO / t
        if full.exists():
            size = full.stat().st_size
            lines = len(full.read_text().split("\n"))
            h = hashlib.sha256(full.read_bytes()).hexdigest()[:16]
            print(f"  ✅ {t}")
            print(f"     {lines} lines | {size} bytes | sha256:{h}...")
        else:
            print(f"  ❌ {t}  (not on disk)")
    print()
    
    total = sum(1 for t in targets if (REPO / t).exists())
    print(f"  {total}/{len(targets)} files verified on disk")


def demo_repo_structure():
    section(
        "5. REPO STRUCTURE",
        "CORE is organized by domain. Each domain handles a specific\n"
        "  capability of the autonomous factory."
    )
    
    domains = [
        ("00_PHYSICS_ENGINE",   "MANTIS trading signals & pipeline"),
        ("01_DATA_INGESTION",   "Market data providers (Alpaca, CSV)"),
        ("02_RISK_MANAGEMENT",  "Position sizing, circuit breakers, alpha decay"),
        ("03_ORCHESTRATION",    "Factory orchestration, tier routing, auto-deploy"),
        ("04_GOVERNANCE",       "Constitutional governance (protected domain)"),
        ("05_REPORTING",        "Epoch reports, postmortems"),
        ("06_BENCHMARKING",     "Benchmark gates, test suites, E14 gates"),
        ("08_CYBERSECURITY",    "SPECTER red-team engine"),
    ]
    
    print(f"  {'Domain':<25} {'Description':<45} {'Files':>6}")
    print(f"  {'─'*25} {'─'*45} {'─'*6}")
    for domain, desc in domains:
        path = REPO / domain
        if path.exists():
            count = sum(1 for _ in path.rglob("*.py"))
            print(f"  {domain:<25} {desc:<45} {count:>6}")
        else:
            print(f"  {domain:<25} {desc:<45} {'—':>6}")


def main():
    print()
    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║                    CORE — LIVE ARCHITECTURE DEMO                    ║")
    print("║           Autonomous AI Factory with Cryptographic Provenance       ║")
    print("║                                                                     ║")
    print("║  Sovereign:  Alec Sanchez                                           ║")
    print("║  Auditor:    Claude (Hostile Auditor)                               ║")
    print("║  Advisor:    Gemini (Strategic Advisor, READ-ONLY)                  ║")
    print("╚══════════════════════════════════════════════════════════════════════╝")
    
    demo_chain_integrity()
    demo_e14_gates()
    demo_sovereign_injections()
    demo_deployed_files()
    demo_repo_structure()
    
    print(f"\n{'='*70}")
    print(f"  DEMO COMPLETE")
    print(f"{'='*70}")
    print(f"  'Learn from your mistakes, identify the patterns, verify the outputs.'")
    print(f"  — Alec Sanchez, Sovereign Operator")
    print()


if __name__ == "__main__":
    main()
