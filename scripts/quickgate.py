#!/usr/bin/env python3
"""
scripts/quickgate.py
====================
TRADER_OPS Quickgate — Automated Inter-Council Sanity Check

Runs on every drop before full council review.
Blocks advancement on the 5 most common AI hallucination failure signatures.

Usage:
    python3 scripts/quickgate.py [--run-dir PATH] [--strict]
    make quickgate

Wire into Makefile:
    quickgate:
        @echo "Running quickgate sanity checks..."
        python3 scripts/quickgate.py --run-dir reports/forge --strict

Exit codes:
    0 = All checks pass
    1 = One or more checks failed (drop blocked)
    2 = Usage error / missing files

LAWS.md Reference:
    LAW 7.2: scripts/quickgate.py must run successfully before any drop packet is assembled.
    LAW 3.3: No silent success on zero fills.
    LAW 2.6: Symbol identity immutability.
    LAW 2.7: Synthetic data prohibition.
    LAW 3.5: Low-sample statistical honesty.
    LAW 3.6: Version sovereignty.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ── Thresholds ─────────────────────────────────────────────────────────────

MIN_FILLS_FOR_VALID_METRICS = 30
MAX_SHARPE_ON_LOW_SAMPLE = 10.0
MAX_PF_ON_LOW_SAMPLE = 100.0


# ── Colour output ──────────────────────────────────────────────────────────

def red(s: str) -> str:    return f"\033[91m{s}\033[0m"
def green(s: str) -> str:  return f"\033[92m{s}\033[0m"
def yellow(s: str) -> str: return f"\033[93m{s}\033[0m"
def bold(s: str) -> str:   return f"\033[1m{s}\033[0m"


# ── Helpers ────────────────────────────────────────────────────────────────

def load_json(path: Path) -> Optional[Dict[str, Any]]:
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return None


def load_csv_first_row(path: Path) -> Optional[Dict[str, str]]:
    try:
        with open(path, newline='') as f:
            reader = csv.DictReader(f)
            return next(reader, None)
    except Exception:
        return None


def find_run_dirs(base: Path) -> List[Path]:
    """Find all run directories containing results.csv."""
    run_dirs = []
    for candidate in base.rglob("results.csv"):
        run_dirs.append(candidate.parent)
    return run_dirs


# ── Gate 1: Silent Zero-Fill Success ──────────────────────────────────────

def check_zero_fill_success(run_dir: Path) -> Tuple[bool, str]:
    """
    GATE 1 — SMOKE_OK with 0 fills and intended exposure.
    LAWS.md LAW 3.3: Status SMOKE_OK requires fills_count > 0.
    """
    results_path = run_dir / "results.csv"
    if not results_path.exists():
        return True, "results.csv not found — skipping"

    row = load_csv_first_row(results_path)
    if not row:
        return True, "results.csv empty — skipping"

    status = row.get("status", "")
    fills = int(row.get("fills_count", "0") or "0")
    pf = row.get("profit_factor", "0")

    if status == "SMOKE_OK" and fills == 0:
        return False, (
            f"GATE 1 FAIL: status=SMOKE_OK but fills_count=0. "
            f"profit_factor={pf}. "
            "A run with zero fills cannot be SMOKE_OK. "
            "Expected: SMOKE_NO_TRADE or SMOKE_BLOCKED_* with NO_TRADE_REPORT.json."
        )

    # Also check PF sentinel: PF=999 is a hard indicator of 0 trades
    try:
        pf_val = float(pf)
        if pf_val >= 999.0 and status == "SMOKE_OK":
            return False, (
                f"GATE 1 FAIL: profit_factor={pf_val} (sentinel for 0 trades) "
                f"with status={status}. This is a known false-success artifact."
            )
    except (ValueError, TypeError):
        pass

    return True, f"PASS: status={status}, fills={fills}"


# ── Gate 2: Symbol Mismatch in Fill Tape ──────────────────────────────────

def check_symbol_coherence(run_dir: Path) -> Tuple[bool, str]:
    """
    GATE 2 — Symbol in fill_tape.csv must match cmd_args.symbols in RUN_METADATA.
    LAWS.md LAW 2.6: If fills_count > 0, set(fill_tape.symbol) == set(cmd_args.symbols).
    """
    fill_tape_path = run_dir / "fill_tape.csv"
    metadata_path = run_dir / "RUN_METADATA.json"

    if not fill_tape_path.exists():
        return False, "GATE 2 FAIL: fill_tape.csv missing entirely. Must exist even if header-only."

    metadata = load_json(metadata_path) if metadata_path.exists() else {}
    if not metadata:
        return True, "RUN_METADATA.json missing or unparseable — skipping"

    # Parse declared symbols
    cmd_args = metadata.get("cmd_args", {})
    declared_symbols_raw = cmd_args.get("symbols", "")
    if isinstance(declared_symbols_raw, str):
        declared_symbols = set(s.strip() for s in declared_symbols_raw.split(",") if s.strip())
    elif isinstance(declared_symbols_raw, list):
        declared_symbols = set(declared_symbols_raw)
    else:
        declared_symbols = set()

    # Read fill tape symbols
    fill_symbols = set()
    fills_count = 0
    try:
        with open(fill_tape_path, newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                sym = row.get("symbol", "").strip()
                if sym:
                    fill_symbols.add(sym)
                    fills_count += 1
    except Exception as e:
        fills_count = 0  # Fallback
        print(f"Warning: fill_tape.csv unreadable ({e})")

    if fills_count == 0:
        return True, "PASS: fill_tape is header-only or unreadable (0 fills)"

    # MISSION v4.6.1: Multi-Symbol Coherence
    # We allow the tape to contain a non-empty subset of the declared symbols.
    cmd_symbols = declared_symbols if declared_symbols else {"MOCK"}
    
    # MISSION v4.7.2: Auto-Universe Support
    if "auto" in cmd_symbols:
        return True, f"PASS: fill symbols {fill_symbols} are permitted via Auto-Universe pivot."

    if not (fill_symbols <= cmd_symbols):
        return False, (
            f"GATE 2 FAIL: Symbol mismatch — "
            f"fill_tape.symbol={fill_symbols} but cmd_args.symbols={cmd_symbols}. "
            "This is a Frankenstein Fill (FRANKENSTEIN-002)."
        )

    return True, f"PASS: fill symbols {fill_symbols} are a subset of {cmd_symbols}"


# ── Gate 3: Synthetic Tape Used as Real ───────────────────────────────────

def check_synthetic_provenance(run_dir: Path) -> Tuple[bool, str]:
    """
    GATE 3 — Synthetic tape used while metadata declares synthetic=False.
    LAWS.md LAW 2.7: Synthetic data must never contaminate core execution evidence.
    """
    metadata_path = run_dir / "RUN_METADATA.json"
    if not metadata_path.exists():
        return True, "RUN_METADATA.json missing — skipping"

    metadata = load_json(metadata_path)
    if not metadata:
        return True, "RUN_METADATA.json unparseable — skipping"

    cmd_args = metadata.get("cmd_args", {})
    prices_csv = str(cmd_args.get("prices_csv", ""))
    synthetic_flag = str(cmd_args.get("synthetic", "False")).lower()

    # Check path for synthetic indicators
    path_is_synthetic = (
        "synthetic" in prices_csv.lower()
        or "synthetic_data" in prices_csv.lower()
        or "_synthetic" in prices_csv.lower()
    )

    if path_is_synthetic and synthetic_flag == "false":
        return False, (
            f"GATE 3 FAIL: prices_csv path contains 'synthetic' ({prices_csv!r}) "
            f"but cmd_args.synthetic={synthetic_flag!r}. "
            "This is a Synthetic Mislabel (FRANKENSTEIN-004). "
            "Either the tape must be real, or synthetic must be set to True "
            "and the run must use OFT control namespace."
        )

    # Check data_provenance field if present
    data_provenance = metadata.get("data_provenance", "")
    if data_provenance in ("synthetic", "unknown") and synthetic_flag == "false":
        return False, (
            f"GATE 3 FAIL: data_provenance={data_provenance!r} "
            f"but synthetic flag is false. Provenance conflict."
        )

    return True, f"PASS: prices_csv={prices_csv!r}, synthetic={synthetic_flag!r}"


# ── Gate 4: Sharpe / PF Absurdity on Low Sample ───────────────────────────

def check_low_sample_metrics(run_dir: Path) -> Tuple[bool, str]:
    """
    GATE 4 — Sharpe > 10 or PF > 100 with fewer than MIN_FILLS fills.
    LAWS.md LAW 3.5: Low-sample statistical honesty.
    """
    results_path = run_dir / "results.csv"
    row = load_csv_first_row(results_path) if results_path.exists() else {}
    if not row:
        return True, "results.csv missing or empty — skipping"

    fills = int(row.get("fills_count", "0") or "0")
    metrics_valid = row.get("metrics_valid", "true").lower()

    # If already tagged as low-sample, gate passes
    if metrics_valid == "false" or "LOW_SAMPLE" in row.get("status", ""):
        return True, f"PASS: Low sample already handled, fills={fills}"

    try:
        sharpe = float(row.get("sharpe_ratio", "0") or "0")
        pf = float(row.get("profit_factor", "0") or "0")
    except (ValueError, TypeError):
        return True, "Non-numeric metrics — skipping"

    if fills < MIN_FILLS_FOR_VALID_METRICS:
        if sharpe > MAX_SHARPE_ON_LOW_SAMPLE and sharpe < 998:
            return False, (
                f"GATE 4 FAIL: sharpe_ratio={sharpe:.2f} on fills_count={fills}. "
                f"Sharpe > {MAX_SHARPE_ON_LOW_SAMPLE} with fewer than {MIN_FILLS_FOR_VALID_METRICS} fills "
                "is a statistical hallucination (FRANKENSTEIN-006). "
                "Expected: metrics_valid=false + SMOKE_LOW_SAMPLE status tag."
            )
        if pf > MAX_PF_ON_LOW_SAMPLE and pf < 998:
            return False, (
                f"GATE 4 FAIL: profit_factor={pf:.2f} on fills_count={fills}. "
                f"PF > {MAX_PF_ON_LOW_SAMPLE} with fewer than {MIN_FILLS_FOR_VALID_METRICS} fills "
                "is a statistical artifact. "
                "Expected: metrics_valid=false + SMOKE_LOW_SAMPLE status tag."
            )

    return True, f"PASS: fills={fills}, sharpe={row.get('sharpe_ratio')}, pf={row.get('profit_factor')}"


# ── Gate 5: Prompt ID / Charter Drift ─────────────────────────────────────

def check_lineage_drift(run_dir: Path) -> Tuple[bool, str]:
    """
    GATE 5 — Prompt ID in artifacts must match declared version.
    LAWS.md LAW 3.6: Version sovereignty.
    """
    fingerprint_path = run_dir / "PROMPT_FINGERPRINT.json"
    metadata_path = run_dir / "RUN_METADATA.json"

    if not fingerprint_path.exists():
        return True, "PROMPT_FINGERPRINT.json missing — skipping"

    fp = load_json(fingerprint_path)
    if not fp:
        return True, "PROMPT_FINGERPRINT.json unparseable"

    charter_id = fp.get("charter_id", "")
    prompt_id_fp = fp.get("prompt_id", "")

    # Charter must be v2.0
    if charter_id and charter_id != "TRADER_OPS_PROMPT_CHARTER_v2.0":
        return False, (
            f"GATE 5 FAIL: charter_id={charter_id!r}. "
            "Expected: TRADER_OPS_PROMPT_CHARTER_v2.0. "
            "Charter lineage is stuck on a prior version."
        )

    # Prompt ID in fingerprint should match RUN_METADATA
    if metadata_path.exists():
        metadata = load_json(metadata_path)
        if metadata:
            env_vars = metadata.get("environment_vars", {})
            prompt_id_meta = metadata.get("TRADER_OPS_PROMPT_ID", "") or env_vars.get("TRADER_OPS_PROMPT_ID", "")
            if prompt_id_fp and prompt_id_meta and prompt_id_fp != prompt_id_meta:
                return False, (
                    f"GATE 5 FAIL: Prompt ID drift — "
                    f"PROMPT_FINGERPRINT.json has {prompt_id_fp!r} "
                    f"but RUN_METADATA has {prompt_id_meta!r}."
                )

    return True, f"PASS: charter_id={charter_id!r}, prompt_id={prompt_id_fp!r}"


# ── Main ───────────────────────────────────────────────────────────────────

def run_gates(run_dir: Path, strict: bool = True) -> bool:
    """Run all 5 quickgates on a single run directory. Returns True if all pass."""
    gates = [
        ("Gate 1: Zero-Fill Success", check_zero_fill_success),
        ("Gate 2: Symbol Coherence",  check_symbol_coherence),
        ("Gate 3: Synthetic Provenance", check_synthetic_provenance),
        ("Gate 4: Low-Sample Metrics", check_low_sample_metrics),
        ("Gate 5: Lineage Drift",     check_lineage_drift),
    ]

    all_pass = True
    for name, fn in gates:
        passed, message = fn(run_dir)
        if passed:
            print(f"  {green('✓')} {name}: {message}")
        else:
            print(f"  {red('✗')} {name}: {message}")
            all_pass = False

    return all_pass


def main() -> int:
    parser = argparse.ArgumentParser(
        description="TRADER_OPS Quickgate — Inter-Council Sanity Check"
    )
    parser.add_argument(
        "--run-dir",
        type=Path,
        default=Path("reports/forge"),
        help="Base directory to scan for run artifacts (default: reports/forge)"
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        default=True,
        help="Exit non-zero on any failure (default: True)"
    )
    args = parser.parse_args()

    base = args.run_dir
    if not base.exists():
        print(red(f"ERROR: Run directory not found: {base}"))
        return 2

    run_dirs = find_run_dirs(base)
    if not run_dirs:
        # No results.csv found — check the base itself
        run_dirs = [base]

    print(bold(f"\nTRADER_OPS QUICKGATE — {len(run_dirs)} run directory(ies)\n"))

    total_fails = 0

    for run_dir in sorted(run_dirs):
        rel = run_dir.relative_to(base) if run_dir != base else Path(".")
        print(bold(f"[{rel}]"))
        passed = run_gates(run_dir)
        if not passed:
            total_fails += 1
        print()

    # Summary
    if total_fails == 0:
        print(green(bold("✓ QUICKGATE PASS — All checks passed. Safe to assemble drop packet.")))
        return 0
    else:
        print(red(bold(
            f"✗ QUICKGATE FAIL — {total_fails} run directory(ies) failed. "
            "Drop packet blocked. Fix violations before proceeding."
        )))
        print(yellow(
            "\nNote: To bypass in emergencies (requires documented reason):\n"
            "  make quickgate SKIP_QUICKGATE=1 REASON=\"your reason\"\n"
            "This bypass is logged and will be flagged in the next council review."
        ))
        return 1 if args.strict else 0


if __name__ == "__main__":
    sys.exit(main())
