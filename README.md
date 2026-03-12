# TRADER_OPS — Institutional Trading Strategy Harness
Version: v9.9.43 | Charter: v2.0 | Owner: Alec

## Overview
TRADER_OPS is a high-fidelity, sovereign validation engine for institutional-grade trading strategies. 
It enforces strict physics-based execution, sovereign governance gates, and verifiable data provenance 
under the strictures of the [THE BASECAMP PROTOCOL](docs/THE_BASECAMP_PROTOCOL.md) (Adversarial Governance Framework). 
to eliminate overfitting, survival bias, and execution leakage.

## Core Mandates
1. **Physics Enforcement**: Strict integer-lot futures execution with mandatory friction (slippage/commission).
2. **Sovereign Governance**: Strict write-gates preventing Quarantine artifacts from contaminating Certification reports.
3. **Data Provenance**: Merkle-root verification of all input datasets via verifiable manifests.
4. **Fiduciary Math**: Hardened annualization and P&L logic across all asset classes.

## Verification
To verify the integrity of this drop:
1. Ensure `sovereign.pub` is present in the `keys/` directory.
2. Run the audit pipeline:
   ```bash
   make verify
   ```
3. Check the `data_manifest.json` against the local `data/` directory for hash consistency.

## Reproducing the Drop
To reproduce the bit-perfect drop packet:
1. Initialize the virtual environment.
2. Execute the build command (requires `TRADER_OPS_PROMPT_ID`):
   ```bash
   TRADER_OPS_PROMPT_ID=TRADER_OPS_MASTER_IDE_REQUEST_v4.7.2 make build
   ```
3. Compare the resulting ZIP SHA256 against the `DROP_PACKET_SHA256_v4.7.2.txt`.

## Governance
This project operates under strict Tier Governance. 
Certificates are only issued to strategies that pass all 6 Fortress Protocol gates.
Quarantine strategies are strictly isolated from the certification path.
