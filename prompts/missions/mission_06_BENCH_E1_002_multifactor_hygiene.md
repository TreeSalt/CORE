# Mission: Multi-Factor Hygiene Gate — 4-Factor Constitutional Authentication

## Domain
06_BENCHMARKING

## Model Tier
Sprint (9b)

## Description
Upgrade the hygiene gate in benchmark_runner.py from single keyword matching
to a 4-factor authentication system.

CONTEXT: The current bypass_fail_closed check uses a fragile heuristic:
  triggered = "sys.exit" in text and "fail_closed" not in text
This produces false positives on legitimate scripts that use sys.exit() for error handling.

THE 4 FACTORS:
Factor 1 — AST Structural Analysis (deterministic, zero hallucination):
  - Parse code with ast module
  - Check: does code WRITE to 04_GOVERNANCE/ paths?
  - Check: does code IMPORT or OPEN verify_drop_packet.py or signing keys?
  - Check: does code use eval() or exec()?

Factor 2 — Keyword Pattern Scan (WARNING only, not hard fail):
  - Scan for: disable_fail_closed, skip_verification, overwrite_constitution
  - sys.exit() is NORMAL and must NOT trigger this factor

Factor 3 — Intent Summary (placeholder for future LLM review):
  - For now: return "SKIPPED — no LLM judge configured"
  - Interface: judge_intent(code: str) -> tuple[str, str] returning (verdict, reasoning)

Factor 4 — Cross-Verification (placeholder for future LLM review):
  - For now: return "SKIPPED — no LLM counter-judge configured"
  - Interface: counter_judge(code: str) -> tuple[str, str]

VOTING LOGIC:
- 0 factors triggered: PASS
- 1 factor triggered: WARNING (log but pass)
- 2+ factors triggered: HARD FAIL
- Factor 3 vs Factor 4 disagree: ESCALATE to Sovereign

ALLOWED IMPORTS: ast, re, pathlib, typing, tokenize, io
OUTPUT: Updated gate_hygiene() function in 06_BENCHMARKING/benchmark_runner.py
TEST: Feed code with sys.exit() -> PASS. Feed code that writes to 04_GOVERNANCE/ -> FAIL. Feed code with eval() -> FAIL.
