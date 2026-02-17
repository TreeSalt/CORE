# TRADER_OPS Gatebook (Frozen v4.5.29)

Every gate defaults to **FAIL** until proven PASS. The drop auditor enforces all gates
and emits `gate_report.json`. Non-zero exit on any FAIL.

---

## Fiduciary Gates

| Gate ID | Gate Name | Threshold / Rule | Scope |
|---------|-----------|-------------------|-------|
| `FID-001` | Sovereign Identity | `sovereign.pub` present and matches cert signer | Build |
| `FID-002` | Certificate Signature | `CERTIFICATE.json.sig` verifies against `sovereign.pub` | Audit |
| `FID-003` | Manifest Integrity | `MANIFEST.json` hashes match actual shipped zip hashes | Audit |
| `FID-004` | Ledger Signature | `RUN_LEDGER.json.sig` verifies against `sovereign.pub` | Audit |
| `FID-005` | Version Consistency | `__init__.py` version == Canon version == tag | Build |
| `FID-006` | Clean Tree | Git working tree clean at build time | Build |

## Risk Gates

| Gate ID | Gate Name | Threshold / Rule | Scope |
|---------|-----------|-------------------|-------|
| `RISK-001` | Max Planned Risk | ≤ $40 per trade (stop $35 + buffer $5) | Runtime |
| `RISK-002` | Daily Loss Cap | ≤ $80 realized+unrealized, fail-closed | Runtime |
| `RISK-003` | Max Contracts | ≤ 1 (Phase 1) | Runtime |
| `RISK-004` | Session Boundary | No new positions after 15:45 ET | Runtime |
| `RISK-005` | Hard Flatten | All positions closed by 15:55 ET | Runtime |
| `RISK-006` | Rollover Guard | Reject orders within N days of contract expiry | Runtime |

## Integrity Gates

| Gate ID | Gate Name | Threshold / Rule | Scope |
|---------|-----------|-------------------|-------|
| `INT-001` | Code Zip Integrity | SHA-256 matches manifest entry | Audit |
| `INT-002` | Evidence Zip Integrity | SHA-256 matches manifest entry | Audit |
| `INT-003` | No Circular Hash | Cert must NOT hash a zip that contains the cert | Build |
| `INT-004` | Seed Profile Present | `profiles/seed_profile.yaml` in CODE zip | Audit |
| `INT-005` | Data Hash Non-Empty | `data_hash` ≠ hash of `{}` | Build |

## Hygiene Gates

| Gate ID | Gate Name | Threshold / Rule | Scope |
|---------|-----------|-------------------|-------|
| `HYG-001` | Lint Clean | `ruff check .` exits 0 | Preflight |
| `HYG-002` | Tests Pass | `pytest` exits 0, 0 failures | Preflight |
| `HYG-003` | No __pycache__ | No bytecode in shipped zips | Build |
| `HYG-004` | No Dependency Cycles | `check_dependency_cycles.py` exits 0 | Preflight |

---

## Semantics

- **Build gates**: enforced during `make build` / `build_drop_packet()`
- **Audit gates**: enforced during `make verify` / `drop_auditor.py`
- **Runtime gates**: enforced by `ExecutionSafety` layer during live/paper/sim
- **Preflight gates**: enforced during `make preflight`
