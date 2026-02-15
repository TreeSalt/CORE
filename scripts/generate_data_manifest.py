#!/usr/bin/env python3
"""
scripts/generate_data_manifest.py

Tier 1 Evidence Credibility:
Walks the `data/` directory and creates a cryptographic manifest of the dataset.
Returns the Merkle Root of the manifest as the "Data Hash".
"""
import argparse
import hashlib
import json
from pathlib import Path
from typing import Dict


def hash_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            h.update(chunk)
    return h.hexdigest()

def generate_manifest(data_root: Path) -> Dict[str, str]:
    manifest = {}
    if not data_root.exists():
        # Handle "Synthetic Only" runs where data dir might be missing
        return {}

    for path in sorted(data_root.rglob("*")):
        if path.is_file() and not path.name.startswith("."):
            rel_path = path.relative_to(data_root).as_posix()
            manifest[rel_path] = hash_file(path)
    return manifest

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument("--out", type=Path, default=Path("DATA_MANIFEST.json"))
    args = parser.parse_args()

    print(f"🔍 Auditing Data Directory: {args.data_dir}")
    manifest = generate_manifest(args.data_dir)
    
    # Calculate Merkle Root of the Manifest itself
    manifest_bytes = json.dumps(manifest, sort_keys=True).encode("utf-8")
    merkle_root = hashlib.sha256(manifest_bytes).hexdigest()

    output = {
        "merkle_root_sha256": merkle_root,
        "files": manifest
    }

    with open(args.out, "w") as f:
        json.dump(output, f, indent=2, sort_keys=True)

    print(f"✅ Data Manifest Generated: {args.out}")
    print(f"🔐 Data Merkle Root: {merkle_root[:8]}")

if __name__ == "__main__":
    main()
