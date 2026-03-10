#!/usr/bin/env python3
"""
scripts/run_loop.py — AOS Autonomous Factory Agent
===================================================
Constitutional Requirement: Phase 1 — 90% Agentic Operation
Ratified: TRADER_OPS Supreme Council — 2026-03-10

PURPOSE:
  Closes the human-in-the-loop gap between the Semantic Router and the
  Benchmark Runner. You invoke this once per mission. It runs until it
  has a result worth your attention, then stops and waits for you.

  YOU only need to act when:
    1. A HARD FAIL occurs (constitutional violation) — requires your diagnosis
    2. Max retries exhausted — requires your decision on how to proceed
    3. A proposal PASSES — requires your ratification to advance

  Everything else — routing, benchmarking, retry logic, failure analysis,
  escalation packaging — is handled autonomously.

FLOW:
  1. Route mission → get proposal
  2. Benchmark proposal
  3. On PASS → write sovereign decision packet, notify, halt
  4. On SOFT FAIL → analyze failures, re-route with corrective context, retry
  5. On HARD FAIL → escalate immediately, no retry
  6. On MAX_RETRIES → escalate with full audit trail, halt

CONSTITUTIONAL CONSTRAINTS:
  - Max retries is sovereign-configurable, default 2 (never infinite)
  - No auto-ratification — PASS still requires human sign-off
  - All attempts logged to ERROR_LEDGER and run_loop state file
  - FAIL-CLOSED on any unexpected exception

USAGE:
  python3 scripts/run_loop.py \\
    --domain 01_DATA_INGESTION \\
    --task "design_data_multiplexer" \\
    --mission data_multiplexer_v1.md \\
    --type ARCHITECTURE \\
    --max-retries 2
"""

from __future__ import annotations

import argparse
import json
import logging
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# ── PATHS ─────────────────────────────────────────────────────────────────────
REPO_ROOT         = Path(__file__).resolve().parents[1]
ERROR_LEDGER      = REPO_ROOT / "docs" / "ERROR_LEDGER.md"
RUN_LOOP_STATE    = REPO_ROOT / "orchestration" / "RUN_LOOP_STATE.json"
ESCALATION_DIR    = REPO_ROOT / "08_IMPLEMENTATION_NOTES" / "ESCALATIONS"
ROUTER            = REPO_ROOT / "orchestration" / "semantic_router.py"
BENCHMARK_RUNNER  = REPO_ROOT / "06_BENCHMARKING" / "benchmark_runner.py"
REPORTS_DIR       = REPO_ROOT / "06_BENCHMARKING" / "reports"

# ── LOGGING ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%SZ"
)
log = logging.getLogger("run_loop")

# ── RESULT CODES ──────────────────────────────────────────────────────────────
PASS       = "PASS"
SOFT_FAIL  = "SOFT_FAIL"
HARD_FAIL  = "HARD_FAIL"
ESCALATE   = "ESCALATE"


# ── STATE ─────────────────────────────────────────────────────────────────────

def _load_state() -> dict:
    if not RUN_LOOP_STATE.exists():
        return {"runs": []}
    return json.loads(RUN_LOOP_STATE.read_text())

def _save_state(state: dict) -> None:
    RUN_LOOP_STATE.parent.mkdir(parents=True, exist_ok=True)
    RUN_LOOP_STATE.write_text(json.dumps(state, indent=2))

def _append_error_ledger(msg: str) -> None:
    timestamp = datetime.now(timezone.utc).isoformat()
    ERROR_LEDGER.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(ERROR_LEDGER, "a") as f:
            f.write(f"\n### {timestamp} — RUN LOOP\n{msg}\n")
    except Exception:
        pass


# ── CORE STEPS ────────────────────────────────────────────────────────────────

def invoke_router(domain: str, task: str, mission: str,
                  proposal_type: str, extra_context: str = "") -> tuple[str, str]:
    """
    Invoke the semantic router. Returns (proposal_path, status).
    extra_context is appended to the task string for retry runs.
    """
    task_with_context = f"{task} {extra_context}".strip()
    cmd = [
        sys.executable, str(ROUTER),
        "--domain", domain,
        "--task",   task_with_context,
        "--mission", mission,
        "--type",   proposal_type,
    ]
    log.info(f"Invoking router: domain={domain} task='{task_with_context}' type={proposal_type}")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True,
                                timeout=1200, cwd=str(REPO_ROOT))
        output = result.stdout + result.stderr

        if result.returncode != 0:
            log.error(f"Router FAIL-CLOSED:\n{output}")
            return "", HARD_FAIL

        # Extract proposal path from router output
        for line in output.splitlines():
            if "Proposal written:" in line or "Proposal ready:" in line:
                # "Proposal ready: /path/to/file"
                parts = line.split(":", 1)
                if len(parts) == 2:
                    proposal_path = parts[1].strip()
                    log.info(f"Proposal written: {proposal_path}")
                    return proposal_path, PASS

        log.error(f"Router returned 0 but no proposal path found in output:\n{output}")
        return "", HARD_FAIL

    except subprocess.TimeoutExpired:
        log.critical("Router timed out after 1200s")
        return "", HARD_FAIL
    except Exception as e:
        log.critical(f"Router crashed: {e}")
        return "", HARD_FAIL


def invoke_benchmark(proposal_path: str, domain: str,
                     proposal_type: str) -> tuple[str, str, dict]:
    """
    Invoke the benchmark runner. Returns (result_code, report_path, parsed_result).
    """
    cmd = [
        sys.executable, str(BENCHMARK_RUNNER),
        "--proposal", proposal_path,
        "--domain",   domain,
        "--type",     proposal_type,
    ]
    log.info(f"Invoking benchmark runner: {Path(proposal_path).name}")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True,
                                timeout=600, cwd=str(REPO_ROOT))
        output = result.stdout + result.stderr

        # Extract report path
        report_path = ""
        for line in output.splitlines():
            if "REPORT:" in line:
                report_path = line.split("REPORT:", 1)[1].strip()

        # Parse result
        passed  = "PASSED" in output and result.returncode == 0
        hard    = "HARD FAIL" in output or "HARD_FAIL" in output

        if hard:
            log.critical(f"HARD FAIL detected in benchmark:\n{output}")
            return HARD_FAIL, report_path, {"output": output}

        if passed:
            log.info("Benchmark PASSED ✅")
            return PASS, report_path, {"output": output}

        log.warning(f"Benchmark SOFT FAIL:\n{output}")
        return SOFT_FAIL, report_path, {"output": output}

    except subprocess.TimeoutExpired:
        log.critical("Benchmark runner timed out")
        return HARD_FAIL, "", {}
    except Exception as e:
        log.critical(f"Benchmark runner crashed: {e}")
        return HARD_FAIL, "", {}


def analyze_failures(report_path: str) -> str:
    """
    Read the benchmark report and extract ALL failure reasons including
    pytest tracebacks as corrective context for the next router invocation.
    """
    if not report_path or not Path(report_path).exists():
        return "Previous attempt failed. Ensure all imports are resolvable and no constitutional violations exist."

    report = Path(report_path).read_text()
    failures = []
    in_pytest_output = False

    for line in report.splitlines():
        stripped = line.strip()
        if stripped.startswith("- "):
            failure = stripped[2:]
            failures.append(failure)
            # If pytest failed, also grab the pytest_output section
            if "PYTEST_FAILED" in failure:
                in_pytest_output = True
        elif in_pytest_output and stripped:
            failures.append(stripped)
            if len(failures) > 20:  # cap at 20 lines
                break

    # Also scan for FAILED/ERROR lines directly in the report
    for line in report.splitlines():
        if any(kw in line for kw in ["AssertionError", "ImportError", "FAILED", "ERROR", "assert "]):
            if line.strip() not in failures:
                failures.append(line.strip())
        if len(failures) > 25:
            break

    if not failures:
        return "Previous attempt failed with no specific failure messages. Ensure clean syntax and constitutional compliance."

    context = "CORRECTIVE_CONTEXT from previous failed attempt: " + " | ".join(failures[:10])
    log.info(f"Failure analysis: {context}")
    return context


def write_escalation_packet(domain: str, task: str, proposal_type: str,
                             attempt_log: list, reason: str) -> str:
    """
    Write a human-readable sovereign decision packet for escalation cases.
    Returns the path to the escalation file.
    """
    ESCALATION_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    escalation_path = ESCALATION_DIR / f"ESCALATION_{domain}_{timestamp}.md"

    lines = [
        f"# SOVEREIGN ESCALATION PACKET",
        f"**Domain:** {domain}",
        f"**Task:** {task}",
        f"**Type:** {proposal_type}",
        f"**Timestamp:** {timestamp}",
        f"**Reason:** {reason}",
        f"",
        f"## What Happened",
        f"The autonomous run loop attempted this task and could not resolve it within",
        f"the constitutional retry limit. Human sovereign decision required.",
        f"",
        f"## Attempt Log",
    ]

    for i, attempt in enumerate(attempt_log, 1):
        lines.append(f"\n### Attempt {i}")
        lines.append(f"- **Result:** {attempt.get('result', 'UNKNOWN')}")
        lines.append(f"- **Proposal:** {attempt.get('proposal_path', 'N/A')}")
        lines.append(f"- **Report:** {attempt.get('report_path', 'N/A')}")
        lines.append(f"- **Failures:** {attempt.get('failures', 'N/A')}")

    lines += [
        f"",
        f"## Required Sovereign Action",
        f"1. Review the proposals and reports linked above",
        f"2. Determine root cause (mission too vague? model tier wrong? domain config issue?)",
        f"3. Either:",
        f"   - Rewrite the mission file and re-invoke run_loop.py",
        f"   - Escalate to Claude.ai (Hostile Auditor) with this packet for architectural diagnosis",
        f"   - Manually write the proposal and submit directly to benchmark_runner.py",
        f"",
        f"**This packet is append-only. Do not delete.**",
    ]

    escalation_path.write_text("\n".join(lines))
    log.critical(f"\n{'='*60}")
    log.critical(f"SOVEREIGN ESCALATION REQUIRED")
    log.critical(f"Packet: {escalation_path}")
    log.critical(f"Reason: {reason}")
    log.critical(f"{'='*60}")
    return str(escalation_path)


def write_pass_packet(domain: str, task: str, proposal_type: str,
                      proposal_path: str, report_path: str,
                      attempt_number: int) -> str:
    """
    Write a sovereign ratification packet for passed proposals.
    """
    ESCALATION_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    packet_path = ESCALATION_DIR / f"RATIFICATION_{domain}_{timestamp}.md"

    lines = [
        f"# SOVEREIGN RATIFICATION PACKET",
        f"**Domain:** {domain}",
        f"**Task:** {task}",
        f"**Type:** {proposal_type}",
        f"**Timestamp:** {timestamp}",
        f"**Attempts Required:** {attempt_number}",
        f"**Status:** AWAITING SOVEREIGN RATIFICATION",
        f"",
        f"## Proposal",
        f"`{proposal_path}`",
        f"",
        f"## Benchmark Report",
        f"`{report_path}`",
        f"",
        f"## Required Sovereign Action",
        f"1. Review the proposal at the path above",
        f"2. If satisfied, ratify by changing STATUS in the proposal header from",
        f"   `PENDING_REVIEW` to `RATIFIED`",
        f"3. Commit with: `git add {proposal_path} && git commit -m 'ratify: {domain} {task}'`",
        f"4. The factory will treat RATIFIED proposals as input for the next phase",
        f"",
        f"**Benchmark Score: 1.0 ✅ — The factory has done its job. You do the rest.**",
    ]

    packet_path.write_text("\n".join(lines))
    return str(packet_path)


# ── MAIN LOOP ─────────────────────────────────────────────────────────────────

def run_loop(domain: str, task: str, mission: str,
             proposal_type: str, max_retries: int) -> None:

    log.info("=" * 60)
    log.info("AOS AUTONOMOUS FACTORY RUN LOOP — ONLINE")
    log.info(f"Domain:   {domain}")
    log.info(f"Task:     {task}")
    log.info(f"Mission:  {mission}")
    log.info(f"Type:     {proposal_type}")
    log.info(f"Retries:  {max_retries}")
    log.info("=" * 60)

    state    = _load_state()
    run_id   = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_record = {
        "run_id": run_id, "domain": domain, "task": task,
        "mission": mission, "type": proposal_type,
        "max_retries": max_retries, "attempts": [], "final_result": None
    }

    attempt_log  = []
    extra_context = ""

    for attempt in range(1, max_retries + 2):  # +1 for initial attempt
        log.info(f"\n--- ATTEMPT {attempt}/{max_retries + 1} ---")

        # Step 1: Route
        proposal_path, router_status = invoke_router(
            domain, task, mission, proposal_type, extra_context
        )

        if router_status == HARD_FAIL:
            attempt_log.append({
                "attempt": attempt, "result": HARD_FAIL,
                "proposal_path": "", "report_path": "",
                "failures": "Router FAIL-CLOSED — see ERROR_LEDGER"
            })
            escalation = write_escalation_packet(
                domain, task, proposal_type, attempt_log,
                f"Router FAIL-CLOSED on attempt {attempt}. Check mission file and domain config."
            )
            _append_error_ledger(f"RUN LOOP HARD FAIL: domain={domain} task={task} escalation={escalation}")
            run_record["final_result"] = HARD_FAIL
            state["runs"].append(run_record)
            _save_state(state)
            sys.exit(1)

        # Step 2: Benchmark
        bench_result, report_path, bench_data = invoke_benchmark(
            proposal_path, domain, proposal_type
        )

        # Read failures for logging
        failures = analyze_failures(report_path) if bench_result != PASS else "None"

        attempt_log.append({
            "attempt": attempt, "result": bench_result,
            "proposal_path": proposal_path,
            "report_path": report_path,
            "failures": failures
        })
        run_record["attempts"].append(attempt_log[-1])

        # Step 3: Evaluate result
        if bench_result == PASS:
            packet = write_pass_packet(
                domain, task, proposal_type,
                proposal_path, report_path, attempt
            )
            log.info(f"\n{'='*60}")
            log.info(f"✅ FACTORY RUN COMPLETE — SOVEREIGN RATIFICATION REQUIRED")
            log.info(f"Ratification packet: {packet}")
            log.info(f"{'='*60}")
            _append_error_ledger(
                f"RUN LOOP PASS: domain={domain} task={task} "
                f"attempts={attempt} proposal={proposal_path}"
            )
            run_record["final_result"] = PASS
            state["runs"].append(run_record)
            _save_state(state)
            sys.exit(0)

        if bench_result == HARD_FAIL:
            escalation = write_escalation_packet(
                domain, task, proposal_type, attempt_log,
                f"HARD FAIL (constitutional violation) on attempt {attempt}. No retry permitted."
            )
            _append_error_ledger(
                f"RUN LOOP HARD FAIL: domain={domain} escalation={escalation}"
            )
            run_record["final_result"] = HARD_FAIL
            state["runs"].append(run_record)
            _save_state(state)
            sys.exit(1)

        # SOFT FAIL — analyze and retry if retries remain
        if attempt <= max_retries:
            extra_context = analyze_failures(report_path)
            log.warning(
                f"Soft fail on attempt {attempt}. "
                f"Retrying with corrective context. "
                f"({max_retries - attempt + 1} retries remaining)"
            )
            continue

        # Retries exhausted
        escalation = write_escalation_packet(
            domain, task, proposal_type, attempt_log,
            f"Max retries ({max_retries}) exhausted without passing benchmark."
        )
        _append_error_ledger(
            f"RUN LOOP EXHAUSTED: domain={domain} task={task} "
            f"attempts={attempt} escalation={escalation}"
        )
        run_record["final_result"] = ESCALATE
        state["runs"].append(run_record)
        _save_state(state)
        sys.exit(1)


# ── ENTRY POINT ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="AOS Autonomous Factory Run Loop — Phase 1 Agentic Operation"
    )
    parser.add_argument("--domain",      required=True,
                        help="Domain ID from DOMAINS.yaml")
    parser.add_argument("--task",        required=True,
                        help="Task identifier")
    parser.add_argument("--mission",     required=True,
                        help="Mission filename in prompts/missions/")
    parser.add_argument("--type",        default="IMPLEMENTATION",
                        choices=["IMPLEMENTATION", "ARCHITECTURE"],
                        help="Proposal type")
    parser.add_argument("--max-retries", type=int, default=2,
                        help="Max soft-fail retries before sovereign escalation (default: 2)")
    args = parser.parse_args()

    run_loop(
        domain=args.domain,
        task=args.task,
        mission=args.mission,
        proposal_type=args.type,
        max_retries=args.max_retries,
    )
