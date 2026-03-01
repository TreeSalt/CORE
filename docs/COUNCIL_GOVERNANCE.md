# TRADER_OPS COUNCIL GOVERNANCE CHARTER
# docs/COUNCIL_GOVERNANCE.md
# Version: Living document — updated by council at each major release.
# Binding: Referenced by .agent/LAWS.md. Not SHA-bound (living document).
# Purpose: Defines the multi-agent council process, roles, cadence, and escalation rules.

---

## 1. COUNCIL STRUCTURE

### Role Definitions

| Title | Instance | Mandate |
|---|---|---|
| **Owner / Sovereign Principal** | Alec | Sets doctrine. Defines stop conditions. Controls capital and real-world execution. Final authority. |
| **Architect** | Gemini | Roadmap design. Strategic sequencing. Synthesizes council inputs into master IDE prompts. Emergency brake authority. |
| **Hostile Auditor** | Claude | Evidence-only forensics. Cryptographic verification. Physics validation. Never accepts prose — must be provable from artifacts. |
| **Truth Engineers (×5)** | Solari (CGPT Hive) | Convert doctrine into un-gameable execution gates. Hash-addressing. Float-tolerance checks. Parser-safe tagging. |
| **IDE Agent** | Antigravity | Code implementation. Subject to all laws in .agent/LAWS.md and .agent/PHYSICS.md. |

### Cognitive Division of Labor

**Claude's lane:** Read actual artifact files (CSV, JSON, ZIP contents). Compute physics. Verify cryptographic chains. Identify failure modes that cannot be detected from prose alone. Never accept claimed behavior as evidence — find it in the artifacts.

**Gemini's lane:** Strategic sequencing. Translate findings into ordered prompt structures. Emergency brake decisions. Roadmap management. Synthesis.

**Solari's lane:** Convert high-level findings into implementation-level gates. Float tolerance. Parser safety. Allowed file list constraints. STOP condition auditing. Each instance reads independently before cross-contamination.

**The Owner's lane:** Capital allocation decisions. Real-world broker interactions. Final authorization of version advancement. Decides when to run prompts.

---

## 2. REVIEW CYCLE PROTOCOL

### Standard Release Cycle

```
1. IDE Agent executes Master IDE Request
2. Drop packet assembled (READY_TO_DROP + sidecar SHA)
3. Drop delivered to council
4. Claude performs hostile forensic audit from artifacts
5. Claude findings → Gemini
6. Gemini synthesizes → Round 1 Solari prompt (no cross-contamination)
7. Solari instances submit Round 1 independently
8. Gemini reads all Round 1 → produces revised prompt
9. Gemini revised prompt → Solari for Round 2 review
10. Solari Round 2 → Gemini final synthesis
11. Alec receives final prompt
12. Alec decides: run prompt / hold / escalate
```

### Cadence Rules

**RULE C1:** Full council review at minimum every 5 version increments.
**RULE C2:** No more than 10 versions may advance without a council artifact review.
**RULE C3:** Every drop must pass `make quickgate` before being assembled.
**RULE C4:** Gemini's "emergency brake" authority overrides version advancement without full council review.
**RULE C5:** After an emergency brake, the next release is a purge/hardening release. It must not attempt new features.

### Violation Protocol

If the cadence rules are violated (e.g., 43 versions advance without council review):
1. The next council review is a "full forensic audit" covering all skipped versions.
2. The Architect must produce a summary of what changed in the skipped versions.
3. The Hostile Auditor must verify that no known failure modes regressed in the skipped versions.
4. No new features are authorized until the forensic audit closes.

---

## 3. PROMPT CONSTRUCTION STANDARDS

### Master IDE Request Required Fields

Every prompt submitted to the IDE agent must contain these fields:

```
PROMPT_ID: TRADER_OPS_MASTER_IDE_REQUEST_vX.Y.Z
CHARTER: TRADER_OPS_PROMPT_CHARTER_v2.0 (mandatory)
DATE: YYYY-MM-DD
OWNER: Alec
TARGET_VERSION: vX.Y.Z
BRANCH: release/vX.Y.Z
SCOPE: [P0/P1/P2] (description)

SECURITY MANDATE: (what agent must read first)
EXCLUSIONS: (what agent must NOT do)
CONTEXT: (why this release exists — reference specific violations)
MISSION: (one-paragraph summary of what must be achieved)
ORDER OF OPERATIONS: (numbered steps)
ALLOWED FILE LIST: (exact files — agent must STOP if new files required)
ACCEPTANCE TESTS: (lettered, verifiable from artifacts)
STOP CONDITIONS: (when the agent must halt immediately)
```

### Allowed File List Rules

The allowed file list is a safety constraint, not a courtesy. It exists to prevent scope creep.
- Every file the agent might touch must be in the list.
- If the agent identifies that a fix requires an unlisted file, it must STOP and report.
- "Architecturally contagious" changes (like InstrumentSpec routing through portfolio layers) require explicit expansion of the list before running.
- The Solari hive is responsible for auditing allowed file lists for completeness.

### Acceptance Test Standards

Every acceptance test must be:
- **Verifiable from artifacts** — not from agent-reported behavior.
- **Binary** — pass or fail, no partial credit.
- **Ordered** — earlier tests must pass before later ones matter.
- **Lettered** — A, B, C, etc., for easy reference in council discussions.

The following acceptance tests are mandatory in every prompt:
- One test for artifact existence (.agent/ files, fill_tape.csv)
- One test for symbol coherence (if fills can occur)
- One test for make verify / make quickgate
- One test for the primary mission of the release

---

## 4. STATUS CODE GOVERNANCE

### Adding New Status Codes

New status codes require:
1. Addition to LAWS.md Article V (Status Code Vocabulary)
2. Addition to PHYSICS.md if physics-related
3. Implementation in the engine
4. A corresponding acceptance test in the release prompt
5. Council review in the next cycle

The status code vocabulary is canonical. An IDE agent must never invent status codes not in LAWS.md.

### Status Code Categories (invariants)

| Category | Rule |
|---|---|
| SUCCESS | Requires fills_count > 0 AND symbol coherence AND not low-sample |
| NO_TRADE | Requires NO_TRADE_REPORT.json + fill_tape.csv header |
| BLOCKED | Requires NO_TRADE_REPORT.json + fill_tape.csv header + DATA_REQUIREMENTS.json (if data-related) |
| LOW_SAMPLE | Appended tag only. Does not replace primary status. Sets metrics_valid=false. |

---

## 5. ARTIFACT CHAIN OF CUSTODY

### The Sovereign Binding Chain (invariant)

```
CODE ZIP → SHA256
EVIDENCE ZIP → SHA256
Both SHAs → RUN_LEDGER_INNER.json
git_commit + git_dirty + manifest_sha → RUN_LEDGER_INNER.json
RUN_LEDGER_INNER + all artifacts → MANIFEST.json → SHA256
All → READY_TO_DROP.zip → SHA256 → sidecar .sha256 file
```

This chain must be intact in every drop. The sovereign verifier checks it. Any break = invalid drop.

### .agent/ Files in the Sovereign Binding

.agent/LAWS.md and .agent/PHYSICS.md must appear in MANIFEST.json.
They must be SHA-bound in the sovereign drop hash.
If their content changes without a version increment: invalid drop.
These files are the AI agent's constitution. Their integrity is as important as the code.

### Mission Prompt Files

prompts/missions/TRADER_OPS_MASTER_IDE_REQUEST_vX.Y.Z.txt must exist for every version.
This file must be SHA-bound into the drop packet.
Build fails-closed if the mission prompt file is missing.
The mission prompt file cannot be silently changed after the drop is built.

---

## 6. ESCALATION RULES

### P0 Escalation

A P0 finding triggers mandatory emergency brake. The current release is held.
A purge/hardening release is the next authorized action.
P0 findings include:
- Any fill record with incoherent physics (Frankenstein Fill)
- SMOKE_OK on zero fills with intended exposure
- Synthetic data mislabeled as real in core evidence
- Allowlist bypass without override artifact
- Proposal temporal paradox (fills occurred after 0-exposure proposal)

### P1 Escalation

P1 findings are tracked but do not trigger emergency brake.
They must be resolved within 3 version increments.
Unresolved P1s escalate to P0 after 3 increments.

Current unresolved P1s (as of v4.5.381):
- README version stale (showing v4.5.290)
- periods_per_year hardcoded (should be derived from tape)
- Strategy certification governance (merkle change auto-demotion not implemented)
- .agent/ content underspecified (taxonomy and status vocabulary not yet populated)

---

## 7. OPENLAW / AUTONOMOUS AGENT POLICY

### Current Policy (as of v4.5.382)

OpenClaw and similar autonomous agent orchestration tools are:
- **PROHIBITED** from touching the main TRADER_OPS repo until semantic truth is welded shut.
- **ALLOWED** in read-only observation mode on a sandboxed copy of the repo.
- **PROHIBITED** from running git push or touching secrets.
- **PROHIBITED** from accessing live broker APIs.

### Promotion Criteria for Autonomous Access

An autonomous agent may be granted write access when:
1. Quickgate passes on all recent drops without manual intervention.
2. The Frankenstein taxonomy has no unresolved P0 items.
3. A sandbox run demonstrates deterministic, no-churn behavior over 5+ consecutive runs.
4. The council explicitly authorizes autonomous mode in a mission prompt.

The Operating Mode for autonomous execution is called **Autopilot Mode** in the product.
OpenClaw is a potential implementation tool, not a product concept.
Do not use "OpenClaw" in product documentation, doctrine, or status codes.

---

## 8. CONTINUOUS EVOLUTION MANDATE

This document is a living charter. It must be updated when:
- A new failure mode is identified (add to LAWS.md Article IV Frankenstein Taxonomy)
- A new status code is needed (add to LAWS.md Article V)
- A new instrument is supported (add to PHYSICS.md Section 1)
- The council structure changes (update Section 1 of this document)
- A new governance protocol is adopted (add a new numbered section)

The Architect (Gemini) is responsible for proposing charter updates.
The Hostile Auditor (Claude) is responsible for verifying updates against existing artifacts.
The Owner (Alec) is responsible for final authorization of charter changes.

**The spirit of this charter:**
We are building a fiduciary-grade trading system with real capital. The council exists to ensure
that every claim the system makes about its own behavior is provably true from artifacts.
When the system lies — even by omission, even by sentinel value, even by mislabeled metadata —
we catch it, we document it, and we build gates that make that specific lie structurally impossible.
One gate at a time, we weld the vault shut.
