# Operator's Command Guide
==========================

This document serves as the single source of truth for all system commands within the TRADER_OPS environment.

## 🚀 Quick Start
Run `make help` for a dynamic cheat-sheet of available targets.

## 🩺 Error Management
The system uses **The Archivist** to track, classify, and learn from failures.

- `make show-errors`: Displays the last 20 events from the `ERROR_LEDGER.json`.
- `python3 scripts/archivist.py --log [CAT] [MSG] [GATE]`: Manually log a new incident.
- `python3 scripts/archivist.py --learn [CODE] [SOL]`: Record a new "vaccine" (resolution) to prevent regression.

### Taxonomy
- **Categories**: `INFRA`, `METADATA`, `LOGIC`, `HYGIENE`, `IDENTITY`
- **Gates**: `STARTUP`, `RUNTIME`, `SHUTDOWN`, `RECOVERY`

## 🩹 Self-Healing (The Repo Doctor)
If the repository feels "dirty" or files are missing:
- `make heal`: Runs the `self_heal.py` protocol.
  - Automatically restores missing tracked files.
  - Synchronizes version numbers across manifests.
  - Purges untracked/ignored artifacts (except identity keys).
  - Performs "Git Surgery" to commit authorized mutations.

## 📦 Build & Release
For official Council delivery:
- `make release`: Executes a clean build followed by a Sovereign Audit.
- `make build`: Forges the drop packet in the `dist/` directory.

## 🛡️ Verification
- `make verify`: Comprehensive end-to-end audit (fail-closed).
- `make audit`: Executes the "One True Command" for final validation.
- `make zip-verify`: Validates the static integrity and taxonomy of the drop packet.

## 🧪 Testing & Calibration
- `make test`: Runs the core unit test suite.
- `make test-hardening`: Verifies the Phase 9E execution physics.
- `make chaos`: Initiates the Chaos Monkey stress test suite.

---
*Identity Warden: sovereign.pub found.*
*Fiduciary State: Institutional Gold.*
