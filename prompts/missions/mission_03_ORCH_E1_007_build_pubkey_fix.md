# Mission: Fix Evidence Pubkey Pin in Build System

## Domain
03_ORCHESTRATION

## Model Tier
Sprint (9b)

## Description
Fix the build system (antigravity_harness/forge/build.py) to dynamically compute
the sovereign public key hash instead of using a stale hardcoded value.

CONTEXT: During core drop, the build output shows the WRONG public key hash being pinned.
The forge/build.py is reading a hardcoded or cached hash instead of computing it live.

REQUIREMENTS:
1. Find where forge/build.py reads or sets the public key hash
2. Replace any hardcoded hash string with a dynamic computation
3. The computation MUST use raw bytes: hashlib.sha256(open(path, "rb").read()).hexdigest()
4. The public key path is: keys/sovereign.pub
5. Do NOT hardcode any hash value — always compute at build time
6. Log the computed hash so the operator can verify

ALLOWED IMPORTS: hashlib, pathlib
OUTPUT: Fix in antigravity_harness/forge/build.py
TEST: Assert the function computes a 64-character hex string from keys/sovereign.pub
