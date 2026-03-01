# TRADER_OPS SOVEREIGN LAWS
# docs/constitution/LAWS.md — READ THIS BEFORE WRITING ANY CODE
# Version: Locked at build time. Do not edit without council authorization.
# Binding: This file is included in MANIFEST.json and the sovereign drop hash.
# If the hash of this file does not match the manifest, the build is invalid.

---

## ARTICLE I — FIDUCIARY SOVEREIGNTY

**LAW 1.1 — The Primary Directive**
This system manages real capital ($2,000 USD seed, IBKR cash account). Every decision
must be auditable, reversible, and provably correct from artifacts. If in doubt, FAIL CLOSED.

**LAW 1.2 — Truth by Construction**
An artifact that passes a gate while lying is worse than a failed artifact.
SMOKE_OK with zero fills and intended exposure is the canonical example of this failure.
Never claim success unless the evidence supports it. Status codes must reflect reality.

**LAW 1.3 — Evidence Supremacy**
No claim is valid unless it can be proven from the drop packet artifacts.
Prose descriptions of behavior do not count. If it is not in fill_tape.csv,
it did not happen. If it is not in RUN_METADATA.json, it was not configured.

**LAW 1.4 — Fail-Closed Default**
When uncertain, block and emit a diagnostic. Never silently continue.
A blocked run with a clear reason code is better than a passing run with corrupted physics.

---

## ARTICLE II — PHYSICS LAWS

**LAW 2.1 — Integer Lot Enforcement (Futures)**
Futures contracts are integer units. MES minimum lot = 1 contract. No fractional fills.
Violation: filled_qty=0.6743 on MES. This is a P0 physics breach.
Implementation: int(capital / (price * multiplier)) — if result is 0, do not place order.

**LAW 2.2 — Capital Physics**
MES notional = price_points × $5.00 multiplier.
At 6,970 pts: 1 contract = $34,850 notional.
$2,000 capital / $34,850 = 0.057 contracts → int() = 0 → NO TRADE.
Do not attempt to trade MES with $2,000 capital. Emit SMOKE_NO_TRADE + NO_TRADE_REPORT.json.

**LAW 2.3 — InstrumentSpec Binding**
Every fill record must carry the full InstrumentSpec of the actual symbol being traded.
The spec is the source of truth for: tick_size, qty_step, multiplier, commission_model, fractional_allowed.
Mixing specs (e.g., applying MES tick conventions to an SPY fill) is a Frankenstein Fill.
This is the worst class of failure: it passes automation gates while the physics are wrong.

**LAW 2.4 — Float-Safe Tick Validation**
NEVER use: fill_price % tick_size == 0
This fails on equities (tick=0.01) due to floating-point representation.
It also passes for wrong reasons on cross-spec Frankenstein fills.
ALWAYS use: k = round(price / tick_size); assert abs(price - k * tick_size) <= max(1e-6, tick_size * 1e-4)
Tick_size must come from InstrumentSpec bound to fill.symbol. Not a default. Not a constant.

**LAW 2.5 — Annualization Truth**
periods_per_year must be derived from observed bars_per_day in the actual dataset.
Do not hardcode 252 × 78 = 19,656 (NYSE equity convention).
IBKR MES RTH tape: ~90 bars/day → 252 × 90 = 22,680.
Sharpe computed with wrong periods_per_year is not a Sharpe. It is a distortion.

**LAW 2.6 — Symbol Identity Immutability**
fill_tape.symbol must always equal the symbol declared in cmd_args.symbols for that run.
If fills_count > 0: set(fill_tape.symbol) == set(RUN_METADATA.cmd_args.symbols) — equality, not subset.
If this invariant is violated: SMOKE_BLOCKED_SYMBOL_INCOHERENCE. No exceptions.

**LAW 2.7 — Synthetic Data Prohibition**
Synthetic data (deterministic CSV, random walks, sine waves) must never contaminate
core execution evidence. Synthetic data can ONLY be used in OFT control streams,
explicitly labeled with data_provenance: "control_synthetic", in the isolated reports/forge/oft/ namespace.
If a tape path contains "synthetic" or the file lives under reports/: SMOKE_BLOCKED_SYNTHETIC_DATA.
If data_provenance is "unknown": FAIL CLOSED. Require DATA_REQUIREMENTS.json.

---

## ARTICLE III — GOVERNANCE LAWS

**LAW 3.1 — The Allowlist Is a Physics Gate**
CAPABILITY_SNAPSHOT.allowlist is not a hint. It is the operator-authorized instrument universe.
Default policy: DENY all instruments not in the allowlist.
To trade outside the allowlist: require ALLOWLIST_OVERRIDE.json containing:
  target_version, reason, allowlist, created_at.
The override must be hashed and bound in RUN_METADATA as allowlist_override_applied: true.
Without a bound override: SMOKE_BLOCKED_ALLOWLIST_VIOLATION.

**LAW 3.2 — Trade Proposal Temporal Ordering**
TRADE_PROPOSAL.json and TRADE_PROPOSAL.md must be generated AFTER router weights are computed.
A proposal generated before weights records 0.0 intended exposure as a paper trail.
If fills_count > 0: proposal.intended_exposure_pct must be > 0 at the time of generation.
If fills occurred but the proposal showed 0 exposure: SMOKE_BLOCKED_PROPOSAL_PARADOX.

**LAW 3.3 — No Silent Success on Zero Fills**
Status SMOKE_OK requires: fills_count > 0 AND intended_exposure matched fills.
If intended_exposure > 0 AND fills_count == 0: status = SMOKE_NO_TRADE.
If capital physics blocked execution: emit NO_TRADE_REPORT.json with reason codes.
profit_factor = 999.0 is a sentinel for "no losing trades on zero trades." It is not alpha.

**LAW 3.4 — Universal Diagnostics**
Every SMOKE_BLOCKED_* status MUST unconditionally emit:
  - NO_TRADE_REPORT.json (with reason_codes[], capital_available, instrument_blocked)
  - fill_tape.csv (header-only is acceptable)
  - DATA_REQUIREMENTS.json (if the block is data-related)
These files must appear in the evidence zip. Their existence must be verifiable by the auditor.

**LAW 3.5 — Low-Sample Statistical Honesty**
If round_trip_trades < 20 OR fills_count < 30 OR sessions < 10:
  Set: metrics_valid = false
  Set: metrics_invalid_reason = "LOW_SAMPLE"
  Append to status: SMOKE_LOW_SAMPLE
Do NOT null the numeric fields (breaks parsers). Add the metadata flags instead.
A run with Sharpe > 10 and fewer than 30 fills is a statistical artifact, not alpha.
SMOKE_LOW_SAMPLE runs CANNOT be used for strategy certification or alpha evidence.

**LAW 3.6 — Version Sovereignty**
Every version increment requires a corresponding mission prompt file:
  prompts/missions/TRADER_OPS_MASTER_IDE_REQUEST_vX.Y.Z.txt
Build fails-closed if this file does not exist for the current version.
The mission prompt file must be SHA-bound into the drop packet.
If the hash of the mission prompt changes after the drop is built, the drop is invalid.

**LAW 3.7 — Data Provenance Mandate**
Every dataset used in a run must have a declared provenance:
  data_provenance: "real" | "synthetic" | "control_synthetic" | "control_noise" | "unknown"
If provenance is "unknown": FAIL CLOSED with SMOKE_BLOCKED_UNBOUND_TAPE.
If provenance is "synthetic" and run_type is not OFT control: FAIL CLOSED.
The active tape must appear in ACTIVE_TAPE_MANIFEST.json with path, sha256, first_ts, last_ts, interval.
The active_tape_sha256 must be bound into RUN_METADATA.

**LAW 3.8 — Strategy Certification Governance**
A strategy that changes (merkle root changes) must be automatically demoted to tier: quarantine.
It cannot re-enter tier: lab or tier: certified without a new certification run.
EQ_SENTIMENT_v1 and all new strategies enter as tier: quarantine.
Certified strategies that run on synthetic or low-sample evidence lose certification.

---

## ARTICLE IV — THE FRANKENSTEIN TAXONOMY

These are the known failure modes. An IDE agent reading this document should recognize
and refuse to implement any pattern in this taxonomy.

**FRANKENSTEIN-001: Silent Zero-Fill Success**
Symptom: SMOKE_OK + profit_factor=999.0 + fills_count=0 + intended_exposure > 0
Root cause: No-trade doctrine absent. Engine ran, router wanted exposure, nothing executed, status not updated.
Detection: intended_exposure_bars > 0 AND fills_count == 0 AND status == SMOKE_OK
Required fix: Status → SMOKE_NO_TRADE, emit NO_TRADE_REPORT.json
Status in codebase: FIXED in v4.5.381

**FRANKENSTEIN-002: Cross-Spec Fill**
Symptom: fill_tape.symbol = "MES", cmd_args.symbols = "SPY", fill_price = 593.0 (SPY price range)
Root cause: FillTape inherits symbol from a default/prior run context rather than execution context.
Detection: set(fill_tape.symbol) != set(cmd_args.symbols)
Required fix: FillTape must accept InstrumentSpec at construction; all fields derived from spec.
Status in codebase: TARGET v4.5.382

**FRANKENSTEIN-003: Fractional Futures Lot**
Symptom: filled_qty = 0.6743 on MES (integer-only instrument)
Root cause: Portfolio buy path using cash-based fallback instead of integer lot computation.
Detection: filled_qty % qty_step != 0 (within float tolerance)
Required fix: int(capital / (price * multiplier)) — strict integer enforcement.
Status in codebase: FIXED in v4.5.338

**FRANKENSTEIN-004: Synthetic Mislabel**
Symptom: prices_csv = "reports/forge/synthetic_data/SPY_5m_synthetic.csv", synthetic = "False"
Root cause: Tradability pivot defaults to synthetic tape when no real tape exists, but doesn't update metadata flag.
Detection: tape path contains "synthetic" AND metadata synthetic != "True"
Required fix: If no real tape exists, SMOKE_BLOCKED_NO_REAL_DATA + DATA_REQUIREMENTS.json. Never auto-generate.
Status in codebase: TARGET v4.5.382

**FRANKENSTEIN-005: Proposal Temporal Paradox**
Symptom: TRADE_PROPOSAL.json shows intended_exposure=0%, but fills occurred.
Root cause: Proposal generated at session start before router computes weights.
Detection: fills_count > 0 AND proposal.intended_exposure_pct == 0
Required fix: Generate proposal AFTER router.compute_weights() returns. Gate: fills → proposal exposure > 0.
Status in codebase: TARGET v4.5.382

**FRANKENSTEIN-006: Sharpe Hallucination**
Symptom: sharpe_ratio = 51.02 on 1 trade over 3.5 days.
Root cause: Wrong periods_per_year (19656 instead of ~22450) × single fill × synthetic low-variance data.
Detection: sharpe > 10 AND fills_count < 30
Required fix: Low-sample gate: metrics_valid=false + SMOKE_LOW_SAMPLE when fills<30 OR sessions<10.
Status in codebase: TARGET v4.5.382

**FRANKENSTEIN-007: Decorative Allowlist**
Symptom: CAPABILITY_SNAPSHOT.allowlist = ["MES"] but pivot selects and runs SPY without override.
Root cause: Allowlist read for logging only; not enforced as an execution gate.
Detection: selected_symbol NOT IN allowlist AND no ALLOWLIST_OVERRIDE.json present
Required fix: Default DENY. SMOKE_BLOCKED_ALLOWLIST_VIOLATION unless bound override exists.
Status in codebase: TARGET v4.5.382

**FRANKENSTEIN-008: Unbound Tape**
Symptom: Run produces fills but no DATA_MANIFEST for the tape used. data_hash = "N/A".
Root cause: Viable pivot run does not go through the data manifest generation path.
Detection: data_hash == "N/A" OR "null" in RUN_METADATA
Required fix: ACTIVE_TAPE_MANIFEST.json with sha256 bound to RUN_METADATA.active_tape_sha256.
Status in codebase: TARGET v4.5.382

---

## ARTICLE V — STATUS CODE VOCABULARY

Every status code that the system can emit. An IDE agent must use only these codes.
Do not invent new status codes without updating this file and obtaining council authorization.

### SUCCESS STATES
SMOKE_OK                           — Fills occurred, physics coherent, evidence complete, not low-sample.
SMOKE_OK_LOW_SAMPLE                — Fills occurred, physics coherent, but metrics_valid=false (low trade count).
SMOKE_ASSISTED_BLOCKED             — Fills would have occurred but --authorize not provided (Assisted Mode).

### NO-TRADE STATES
SMOKE_NO_TRADE                     — Router desired exposure but 0 fills due to physics/capital constraints.

### BLOCKED STATES (all require NO_TRADE_REPORT.json + fill_tape.csv header)
SMOKE_BLOCKED_CAPITAL_INSUFFICIENT — Capital too small for minimum tradable unit.
SMOKE_BLOCKED_ALLOWLIST_VIOLATION  — Instrument not in operator allowlist, no valid override present.
SMOKE_BLOCKED_SYMBOL_INCOHERENCE   — fill_tape.symbol != cmd_args.symbols (Frankenstein fill detected).
SMOKE_BLOCKED_SYNTHETIC_DATA       — Tape path contains "synthetic" or data_provenance = "synthetic".
SMOKE_BLOCKED_NO_REAL_DATA         — No real tape exists for viable asset. DATA_REQUIREMENTS.json emitted.
SMOKE_BLOCKED_UNBOUND_TAPE         — Tape exists but not listed in DATA_MANIFEST / data_hash unverifiable.
SMOKE_BLOCKED_PROPOSAL_PARADOX     — fills_count > 0 but proposal.intended_exposure_pct == 0.
SMOKE_BLOCKED_OVERRIDE_UNBOUND     — ALLOWLIST_OVERRIDE.json present but not hash-bound in manifest.

### FAILURE STATES
FAIL_OOS_DEGRADATION               — OOS profit_factor < 1.0.
FAIL_OOS_NO_TRADE                  — OOS fills_count == 0 AND OOS_intended_exposure_bars > 0.

### COMPOSITE TAGS (appended to primary status, do not replace it)
SMOKE_LOW_SAMPLE                   — Appended when fills<30 OR sessions<10. Sets metrics_valid=false.

---

## ARTICLE VI — CANONICAL ARTIFACT CHECKLIST

Every drop packet must contain these artifacts. If any are missing, the drop is INCOMPLETE.
The sovereign verifier checks this list. Missing artifacts cause build failure.

### Per Run Directory (ibkr_smoke/, viable_smoke/, etc.)
  [ ] RUN_METADATA.json          — cmd_args, config_snapshot, data_hash, active_tape_sha256, prompt_id
  [ ] results.csv                — status, fail_gate, fail_reason, profit_factor, fills_count, metrics_valid
  [ ] fill_tape.csv              — ALWAYS present. Header-only if fills_count == 0.
  [ ] TRADE_PROPOSAL.json        — Generated AFTER router weights. target_weights, intended_exposure_pct.
  [ ] TRADE_PROPOSAL.md          — Human-readable wrapper of proposal JSON.
  [ ] equity_curve.csv           — Per-bar equity values.
  [ ] router_trace.csv           — Per-rebalance regime + weight assignments.
  [ ] EVIDENCE_MANIFEST.json     — Lists all files in this run directory with sha256 hashes.
  [ ] SUMMARY.md                 — Human-readable run summary.

### Conditional Artifacts (required when condition is true)
  [ ] NO_TRADE_REPORT.json       — Required when: any SMOKE_BLOCKED_* or SMOKE_NO_TRADE status.
  [ ] DATA_REQUIREMENTS.json     — Required when: SMOKE_BLOCKED_NO_REAL_DATA or SMOKE_BLOCKED_UNBOUND_TAPE.
  [ ] ACTIVE_TAPE_MANIFEST.json  — Required when: any run that uses a data tape.
  [ ] ALLOWLIST_OVERRIDE.json    — Required when: allowlist_override_applied = true.

### Session-Level Artifacts (one per session, not per run)
  [ ] CAPABILITY_SNAPSHOT.json   — Broker capabilities, capital, allowlist.
  [ ] INSTRUMENT_VIABILITY_TABLE.json — Per-instrument viable flag + reason.
  [ ] PROMPT_FINGERPRINT.json    — prompt_id, charter_id (must be v2.0), prompt_sha256.

### Sovereign Artifacts (in drop packet root)
  [ ] RUN_LEDGER_INNER.json      — code_sha256, evidence_sha256, git_commit, git_dirty, manifest_sha256.
  [ ] MANIFEST.json              — Complete file listing with hashes. Includes documentation/constitution files.
  [ ] sovereign.pub              — Public key for signature verification.

---

## ARTICLE VII — PROCESS LAWS

**LAW 7.1 — Council Review Cadence**
Full council review is required at minimum every 5 version increments.
No more than 10 versions may advance without a council artifact review.
Autonomous advancement beyond this threshold is a governance failure, not a feature.

**LAW 7.2 — Quickgate Requirement**
scripts/quickgate.py must run successfully before any drop packet is assembled.
Quickgate checks: (1) SMOKE_OK+0fills, (2) symbol mismatch, (3) synthetic tape, (4) Sharpe>10+low fills, (5) prompt ID drift.
If quickgate fails, the build must fail. No bypass except explicit SKIP_QUICKGATE=1 with documented reason.

**LAW 7.3 — The Purge-Not-Pivot Rule**
A release whose mission is governance/purge (like v4.5.382) must NOT attempt to demonstrate viable trading.
Failing closed on allowlist violation is the CORRECT outcome for a purge release.
An IDE agent that weakens governance gates to make tests pass has violated this law.

**LAW 7.4 — Governance Documents Are Sovereign**
This file (docs/constitution/LAWS.md) and docs/constitution/PHYSICS.md must appear in MANIFEST.json.
They must be SHA-bound in the sovereign drop hash.
If they are modified without a version increment, the build is invalid.
If they do not exist, create them before writing any other code.

**LAW 7.5 — README Version Tracking**
README.md must reflect the current version. A README that is 92 versions behind
(e.g., showing v4.5.290 when codebase is at v4.5.382) is a documentation failure.
The Repo Doctor (self_heal.py) must keep README.md in sync with __init__.py version.
