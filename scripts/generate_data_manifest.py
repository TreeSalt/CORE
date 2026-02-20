#!/usr/bin/env python3
"""
scripts/generate_data_manifest.py

Tier 1 Evidence Credibility:
Walks the `data/` directory and creates a cryptographic manifest of the dataset.
Returns the Merkle Root of the manifest as the "Data Hash".
Supports specifying specific files or scanning the root.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Dict, List

try:
    from antigravity_harness.data.market_tape import MarketTape
except ImportError:
    # Fallback if running outside of package context
    MarketTape = None

def hash_file_or_tape(path: Path) -> str:
    """Compute raw SHA256 hash of file (Strict Manifest Binding)."""
    # Previously used MarketTape semantic hash, but that breaks verify_drop_packet.py
    # which assumes raw file hash. For drop verification, bit-perfect file match is required.
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            h.update(chunk)
    return h.hexdigest()

def generate_manifest(files: List[Path], root: Path) -> Dict[str, str]:
    manifest = {}
    for path in sorted(files):
        if path.is_file() and not path.name.startswith("."):
            try:
                rel_path = path.relative_to(root).as_posix()
            except ValueError:
                # If file is not relative to root (e.g. symlink or external), use name
                rel_path = path.name
            manifest[rel_path] = hash_file_or_tape(path)
    return manifest

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("data"), help="Root directory for relative paths")
    parser.add_argument("--out", type=Path, default=Path("DATA_MANIFEST.json"))
    parser.add_argument("--files", nargs="*", help="Specific files to include (relative to root)")
    args = parser.parse_args()

    # Determine file list
    files_to_hash = []
    if args.files:
        print(f"🔍 Auditing Specific Files: {args.files}")
        for f in args.files:
            p = args.root / f
            if p.is_file():
                files_to_hash.append(p)
            else:
                print(f"⚠️  File not found: {p}")
                sys.exit(1)
    elif args.root.exists():
        print(f"🔍 Auditing Data Directory: {args.root}")
        files_to_hash = [p for p in args.root.rglob("*") if p.is_file()]
    else:
        print(f"⚠️  Root missing: {args.root}")
        # Valid to return empty manifest if root missing and no files specified (e.g. no data run)
        
    manifest = generate_manifest(files_to_hash, args.root)
    
    # Calculate Merkle Root of the Manifest itself
    # P0-C: We need to ensure the manifest binding is strict.
    # The dictionary maps filename -> sha256(content).
    # The merkle root is sha256(json(map)).
    manifest_bytes = json.dumps(manifest, sort_keys=True).encode("utf-8")
    merkle_root = hashlib.sha256(manifest_bytes).hexdigest()

    output = {
        "merkle_root_sha256": merkle_root,
        "file_sha256": manifest, # Renamed key to match verify_drop_packet.py usage
        "files": manifest # Keep legacy key for compatibility just in case, or clearer distinction?
                          # build.py writes this. verify_drop_packet expects file_sha256 usually in similar manifests.
                          # check build.py usage.
    }
    # verify_drop_packet.py P0-C logic: file_sha_map = dm.get("file_sha256", {})
    # Previous version output: "files": manifest.
    # So I should update output to include "file_sha256" or update verifier. 
    # I updated verifier to read `dm.get("file_sha256", {})`. 
    # So I must output `file_sha256`.

    with open(args.out, "w") as f:
        json.dump(output, f, indent=2, sort_keys=True)
        f.write("\n") # POSIX guideline

    print(f"✅ Data Manifest Generated: {args.out}")
    print(f"🔐 Data Merkle Root: {merkle_root[:8]}")

if __name__ == "__main__":
    main()
