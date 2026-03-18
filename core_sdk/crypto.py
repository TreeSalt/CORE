"""core_sdk.crypto — Hash verification utilities. NO private key handling."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from typing import Dict

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def sha256_string(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()

def verify_hash_chain(manifest: dict) -> bool:
    for filepath, expected_hash in manifest.items():
        p = Path(filepath)
        if not p.exists():
            return False
        if sha256_file(p) != expected_hash:
            return False
    return True

def compute_manifest(directory: Path) -> Dict[str, str]:
    manifest = {}
    for p in sorted(directory.rglob("*")):
        if p.is_file():
            manifest[str(p.relative_to(directory))] = sha256_file(p)
    return manifest
