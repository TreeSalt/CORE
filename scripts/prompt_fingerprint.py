#!/usr/bin/env python3
"""
scripts/prompt_fingerprint.py
=============================
Canonicalizes and computes the SHA256 hash of a prompt file.
Generates a JSON fingerprint containing metadata and the hash.

Usage:
  python scripts/prompt_fingerprint.py <prompt_file> --out-dir <dir> --id <prompt_id> --charter <charter_id>
"""

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def canonicalize_content(text: str) -> bytes:
    """
    Canonicalization Rules (Institutional Standard):
    1. LF line endings ONLY.
    2. Strip trailing whitespace from each line.
    3. Ensure exactly one trailing newline at EOF.
    4. UTF-8 encoding.
    """
    lines = text.splitlines()
    # Strip trailing whitespace from each line
    lines = [line.rstrip() for line in lines]
    # Rejoin with LF
    content = "\n".join(lines)
    # Ensure exactly one newline at end
    if content and not content.endswith("\n"):
        content += "\n"
    return content.encode("utf-8")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("prompt_file", type=Path, help="Path to the prompt file")
    parser.add_argument("--out-dir", type=Path, required=True, help="Directory to save PROMPT_FINGERPRINT.json")
    parser.add_argument("--id", required=True, help="Unique Prompt ID")
    parser.add_argument("--charter", required=True, help="Governing Charter ID")
    args = parser.parse_args()

    if not args.prompt_file.exists():
        print(f"❌ Prompt file not found: {args.prompt_file}")
        sys.exit(1)

    # Read and Canonicalize
    raw_text = args.prompt_file.read_text(encoding="utf-8")
    canon_bytes = canonicalize_content(raw_text)
    
    # Compute Hash
    prompt_sha256 = hashlib.sha256(canon_bytes).hexdigest()

    # Generate Fingerprint
    fingerprint = {
        "prompt_id": args.id,
        "charter_id": args.charter,
        "timestamp_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "prompt_sha256": prompt_sha256,
        "canonical_bytes_len": len(canon_bytes)
    }

    # Write Output
    out_path = args.out_dir / "PROMPT_FINGERPRINT.json"
    args.out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(fingerprint, f, indent=2, sort_keys=True)
        f.write("\n")

    print(f"✅ Prompt Fingerprint Secured: {out_path}")
    print(f"🔐 SHA256: {prompt_sha256[:8]}...")

if __name__ == "__main__":
    main()
