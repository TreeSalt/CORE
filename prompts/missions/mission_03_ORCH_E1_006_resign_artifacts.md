# Mission: Re-Sign All Artifacts with Rotated Key

## Domain
03_ORCHESTRATION

## Model Tier
Sprint (9b)

## Description
Build a script that re-signs all existing build artifacts with the current sovereign key.

CONTEXT: After key rotation, all existing .sig files are invalid because they were signed
with the old key. The build system bypasses this with "Council Preview Release" but we need
proper signatures.

REQUIREMENTS:
1. Find all .sig files in dist/ and reports/forge/
2. For each .sig, find the corresponding data file (same name without .sig)
3. Re-sign with: openssl pkeyutl -sign -inkey sovereign.key -in <file> -out <file>.sig
4. Verify each new signature with sovereign.pub
5. Print summary: files re-signed, verification status

CRITICAL: The script reads sovereign.key for signing. This is a SOVEREIGN-ONLY operation.
The script itself must NOT be committed with the key path hardcoded — use CLI argument.

ALLOWED IMPORTS: subprocess, pathlib, sys, argparse, json
OUTPUT: scripts/resign_artifacts.py
TEST: Create a temp file, sign it, verify signature. Assert verification passes.
