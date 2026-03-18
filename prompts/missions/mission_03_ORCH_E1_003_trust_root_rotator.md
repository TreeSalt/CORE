# Mission: Trust Root Key Rotation Script

## Domain
03_ORCHESTRATION

## Model Tier
Sprint (9b)

## Description
Build a trust root rotation script that automates sovereign key rotation across the entire codebase.

CONTEXT (from a REAL incident):
When we rotated the ED25519 sovereign key, the trust root hash was hardcoded in 8 files.
The verifier (scripts/verify_drop_packet.py) hashes the public key file using RAW BYTES:
    hashlib.sha256(open(path, "rb").read()).hexdigest()
But we initially computed the hash using .strip().encode(), which strips the trailing newline.
This mismatch caused core drop to fail with "Trusted public key hash mismatch".

The script must:
1. Read the public key file as RAW BYTES (matching how verify_drop_packet.py reads it)
2. Compute SHA256 of the raw bytes
3. Find ALL files containing the OLD hash (search *.py, *.yaml, *.json recursively)
4. Replace the old hash with the new hash in every file found
5. Print a summary of files modified
6. Verify zero instances of the old hash remain

CRITICAL: The hash MUST be computed from raw bytes: hashlib.sha256(open(path, "rb").read()).hexdigest()
Do NOT use .strip() or .encode() — those change the hash due to trailing newlines.

ALLOWED IMPORTS: hashlib, pathlib, json, sys, re, os
NO EXTERNAL DEPENDENCIES.

OUTPUT: scripts/rotate_trust_root.py
USAGE: python3 scripts/rotate_trust_root.py keys/sovereign.pub [--old-hash OLDHASH]

TEST: 
1. Compute hash of keys/sovereign.pub using raw bytes
2. Assert hash matches expected format (64 hex characters)
3. Create a temporary file containing a fake old hash, run replacement, assert old hash is gone
