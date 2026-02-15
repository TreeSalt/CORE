# Sovereign Build Protocol: The 12 Institutional Gates

This document codifies the "Dragonproof" security standard for TRADER_OPS v4.3.4 (OMEGA). 
Every artifact must pass these 12 gates before being granted Sovereign Status.

## Gate 1: Ledger Presence
The **Fiduciary Ledger** (`RUN_LEDGER_LATEST.json`) must exist and be readable. It serves as the Root of Trust for the entire ensemble.

## Gate 2: Artifact Existence
All files mandated by the Ledger must exist on disk. Any missing artifact constitutes an Epistemological Void.

## Gate 3: Temporal Isomorphism
Every artifact's bit-perfect hash must match the Ledger exactly. This prevents any "in-flight" alteration of zips or aliases.

## Gate 4: Zip Static Integrity
All archives must pass a `testzip` parity check. No binary corruption or partial writes are permitted.

## Gate 5: Fiduciary Attestation
The version specified in the Ledger must match the version in the Code Manifest. Desync constitutes a Schism.

## Gate 6: Builder Registry Lockdown
Only approved Builder IDs (prefixed with `Sovereign` or blessed IDs like `SOLARI_BUILD_AGENT_01`) can authorize a build.

## Gate 7: The Basilisk Gaze (Provenance Verification)
The **Code Manifest** hash is recalculated from its own content and cross-checked against the Ledger binding. Tampering with the manifest itself is detected here.

## Gate 8: The Purity Seal (Exhaustive Zip Equality)
The file set in the Code Zip must match the Manifest's file list exactly. No "stowaway" files or unlisted scripts are allowed.

## Gate 9: Gorgon Stare (Duplicate Entry Protection)
The Zip Central Directory is audited for duplicate filenames. This prevents "shadowing" attacks where a valid file hides a sabotaged one.

## Gate 10: Verifier's Vow (Filter Self-Verification)
`great_filter.py` is part of the manifest. Before checking the code, it recalculates its own on-disk hash to detect "Medusa-style" verifier hijacking.

## Gate 11: Absolute Exhaustive Audit
Every single file in the artifact is audited bit-by-bit against its Manifest hash. No statistical sampling. Total verification.

## Gate 12: Bound Sovereignty (The Kraken Defense)
The Evidence Bundle must contain meta-data binding it to the specific Code Manifest hash it was forged from. Session desync is forbidden.

---
**Status: OMEGA IMMORTAL**
*Sovereignty is the absence of shadows.*
