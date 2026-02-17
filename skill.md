# TRADER_OPS — Antigravity Agent Skill

## Mission
Turn TRADER_OPS into a **trustable research-to-release engine** that can discover, validate, and ship strategies **without lying to itself**.
This repo prioritizes:
1) Reproducibility & auditability (strict mode, deterministic artifacts)
2) Risk governance & gates
3) Only then: alpha discovery and execution integration

## Non-Negotiables (Hard Rules)
- **Never “handwave pass”**: if a gate/auditor fails, fix the root cause or downgrade the claim.
- **Patch discipline**: propose changes as small diffs; avoid broad refactors unless explicitly requested.
- **Strict mode stays ON** unless the user explicitly requests otherwise.
- **No TOS evasion / platform circumvention guidance**. If a venue disallows automation, treat it as disallowed.
- **No secret material**: never introduce private keys, tokens, passwords into the repo or logs.
- **Evidence-first**: every major claim must have an artifact: test, report, manifest, or verifier output.

## Repo Mental Model (What lives where)
- `antigravity_harness/` — orchestration: data fetch, backtests, calibration/sweeps, gate evaluation, reporting
- `antigravity_harness/forge/` — artifact forging: manifests, certification seal, evidence packaging
- `scripts/` — “one-true-command” style entrypoints and verifiers
- `docs/` — architecture + onboarding + ready-to-drop contract
- `tests/` — safety, correctness, regression protection

## “Definition of Done” for any PR/change
A change is done only if:
- Tests pass (or new tests added for the new behavior)
- Any new CLI behavior is documented
- Verifiers still PASS on a fresh run
- Drop packet can be produced and audited

## Commands (Local Workflow)

> **📖 Full command reference: [docs/COMMANDS.md](docs/COMMANDS.md)**

### Quick Reference
- `make all` — Full pipeline (preflight → build → verify)
- `make heal` — Auto-repair versioning and hygiene
- `make commands` — Terminal cheat-sheet
- `make show-errors` — View recent errors (human-friendly)
- `python3 -m antigravity_harness.cli -h` — CLI subcommands
- `python3 -m antigravity_harness.cli info` — Project health status

## Gates (How to treat them)
Gates exist to prevent “pretty but fake” results.
- Gate outcomes must be machine-readable and exported to reports.
- Any new strategy must declare a **gate profile** (e.g., `equity_fortress`, `crypto_profit`) and its thresholds.
- If changing thresholds: explain why, and include a before/after report.

## Adding a new Strategy (Plugin Pattern)
When asked to add strategy logic:
1) Implement strategy as a minimal module/function.
2) Add at least one unit test that fails without the strategy.
3) Add a smoke run entry so it appears in evidence reports.
4) Ensure output fields match report schema (PF, Sharpe, DD, trade_count, fail_gate, fail_reason).

## Data Integrity Rules
- All downloaded datasets must be cached and hashed.
- Any resampling must document timezone/session rules.
- If data is missing/short: fail loudly (no silent truncation).

## Transaction Costs & Reality (Required before “alpha claims”)
Before any “this makes money” claim:
- Slippage model per asset class
- Fees model per venue
- Latency assumptions stated
- Out-of-sample validation protocol declared (walk-forward / purged CV)
- Regime sensitivity check (at least 2 disjoint market regimes)

## Evidence Suite Contract
Evidence must include:
- SUMMARY (human-readable)
- results.csv (machine-readable)
- manifests + hashes
- certificate + signature + pinned public key
- reproduction instructions (exact command lines)

## Agent Response Style (How to communicate)
Default output format:
1) What I observed (facts)
2) What is failing / risky
3) Minimal patch plan
4) Patch diff(s)
5) Verification commands to run

Avoid:
- vague “should be fine”
- giant refactors
- changing 10 things to fix 1 issue
