# TRADER_OPS Decision Log

This log documents the major architectural decisions and "forks in the road" for the TRADER_OPS project. It serves as the long-term memory for the Project's constitutional evolution.

---

## 2026-02-14: Dual-Ledger Sovereignty (v4.4.25)

### Context
Reviewers identified a "Fixed Point Paradox" where the `RUN_LEDGER.json` could not contain its own hash without infinite recursion, yet the Council demands bit-perfect truth-binding of all files inside the drop packet.

### Decision
Separation of the ledger into **INNER** and **OUTER** states.
- **INNER LEDGER**: Embedded inside the drop packet. Contains hashes for Code and Evidence. Excludes the `ready_to_drop` (self) hash.
- **OUTER LEDGER**: Lives on disk in `dist/`. Contains everything in the Inner Ledger PLUS the final hash of the generated zip.

### Trade-offs
- **Pros**: Breaks the recursive loop; enables bit-perfect verification of the internal code/evidence zip from the inner ledger.
- **Cons**: Adds a layer of complexity to the verification gate (must ensure Inner == Outer minus self-hash).

---

## 2026-02-14: Forced Provenance (The Smoke Test Decree)

### Context
The Council found that evidence was being "harvested" (re-used) across builds if not manually cleaned, leading to "stale evidence" that didn't contemporary witness the actual code state.

### Decision
Modified `build.py` to **FORCE** a fresh smoke test run during the forge process.
- Action: RMTREE `reports/forge/smoke_test` before every build.
- Action: Check for version drift between code and generated evidence.

### Trade-offs
- **Pros**: Guarantees that every release contains 100% contemporary proof-of-physics.
- **Cons**: Increases build time by ~30 seconds.

---

## 2026-02-15: The Fiduciary Seal (v4.4.31)

### Context
Provenance alone is insufficient for institution-grade non-repudiation. The Council required a cryptographic "Seal of Approval" that binds the build identity to a verified entity.

### Decision
Implementation of Ed25519 binary signatures for build artifacts.
- **Action**: Generate `CERTIFICATE.json` containing Merkle roots of all artifacts.
- **Action**: Sign using `sovereign.key` and include `CERTIFICATE.json.sig` and `sovereign.pub` in the evidence bundle.
- **Action**: Verifier now enforces signature validity before passing any gate.

### Trade-offs
- **Pros**: Provides absolute cryptographic non-repudiation; allows independent third-party verification.
- **Cons**: Adds dependency on `openssl` for the build process.

---

## 2026-02-15: Solari v4 Remediation (v4.4.41)

### Context
A Solari Council audit identified three specific "Fiduciary Schisms":
1. The Canon Hole (Canon not in manifest).
2. The Memory WAL (WAL not crash-resilient).
3. The Physics Schism (Interval not wired to annualization).

### Decision
Executed "The Dragon's Three Commands":
- **Command I**: Included `COUNCIL_CANON.yaml` in the `PAYLOAD_MANIFEST.json`. This was achieved by carefully sequencing the Manifest generation *after* updating the Canon with the Fingerprint, thereby closing the provenance loop.
- **Command II**: Switched `WriteAheadLog` from `:memory:` to `state/wal.db`.
- **Command III**: Wired `periods_per_year` calculate to the `interval` config field.

### Trade-offs
- **Pros**: Achieves "True Fiduciary Grade" status. Crash recovery is now session-independent.
- **Cons**: Increases implementation complexity in the build-forge sequencer.

---

## 2026-02-15: Automated Dist Hygiene (v4.4.42)

### Context
The `dist/` directory was becoming cluttered with intermediate zips (CODE and EVIDENCE), increasing the risk of shipping the wrong file to the Council.

### Decision
Implemented a "Clean Room" standard for distribution.
- **Action**: Automated `dist/` purge at the start of every build.
- **Action**: Redirection of intermediate artifacts to `reports/forge/build_tmp`.
- **Action**: Curated promotion of only the Master Bundle, Ledger, and Sidecars to the final delivery folder.

### Trade-offs
- **Pros**: Eliminates shipment risk; enforces a strictly clean delivery environment.
- **Cons**: Intermediate files are now ephemeral (unless manually retrieved from build_tmp).

---

## 2026-02-15: Automate Decision Logging: Fixed-Point Sovereignty v4.4.43 (v4.4.43)

### Context
Automated entry captured via Git Provenance during the v4.4.43 forge.

### Decision
No additional context provided.

### Trade-offs
- **Pros**: Guaranteed provenance; zero-effort documentation.
- **Cons**: Depth of log depends on commit message quality.

---

## 2026-02-15: All-Knowing README: Constitutional Centralization and Self-Updating Gateway v4.4.44 (v4.4.44)

### Context
Automated entry captured via Git Provenance during the v4.4.44 forge.

### Decision
No additional context provided.

### Trade-offs
- **Pros**: Guaranteed provenance; zero-effort documentation.
- **Cons**: Depth of log depends on commit message quality.

---

## 2026-02-15: Forge Purity: Fix duplicate manifest zip entry v4.4.45 (v4.4.45)

### Context
Automated entry captured via Git Provenance during the v4.4.45 forge.

### Decision
No additional context provided.

### Trade-offs
- **Pros**: Guaranteed provenance; zero-effort documentation.
- **Cons**: Depth of log depends on commit message quality.
