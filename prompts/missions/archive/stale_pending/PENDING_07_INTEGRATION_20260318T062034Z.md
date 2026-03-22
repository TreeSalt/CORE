# CLOUD TASK PACKAGE
# Model: claude-code | Tier: heavy | Domain: 07_INTEGRATION
# Security: INTERNAL | Cloud-eligible: True

DOMAIN: 07_INTEGRATION
SECURITY_CLASS: INTERNAL
MISSION: # Mission: core-sdk crypto.py — Hash Verification (NO private keys)

## Domain
07_INTEGRATION

## Model Tier
Heavy (27b)

## Description
Create core_sdk/crypto.py with cryptographic VERIFICATION utilities.

CRITICAL SECURITY RULE: This module must NEVER handle private keys.
It provides VERIFICATION ONLY — checking signatures and computing hashes.

EXACT FUNCTIONS:

1. sha256_file(path: Path) -> str — compute SHA256 hex digest of a file
2. sha256_string(data: str) -> str — compute SHA256 hex digest of a string  
3. verify_hash_chain(manifest: dict) -> bool — verify all hashes in a payload manifest match
4. compute_manifest(directory: Path) -> dict — walk directory, compute SHA256 for each file, return {filepath: hash}

DO NOT implement signing. DO NOT import private key files. DO NOT handle ED25519 signing.
ALL imports from Python stdlib ONLY (hashlib, pathlib, typing, json).
NO external dependencies. NO cryptography library.

OUTPUT: core_sdk/crypto.py
TEST: Create a temp file, compute its SHA256, verify it matches hashlib directly.
TASK: 07_SDK_E1_003_crypto
CONSTRAINTS:
  - Proposals only. No direct execution.
  - No writes to 04_GOVERNANCE/
  - No hardcoded credentials
  - Fail closed on any constraint breach
  - Output valid Python code only


INSTRUCTIONS: Execute in Claude Code terminal. Return proposal to 08_IMPLEMENTATION_NOTES/.