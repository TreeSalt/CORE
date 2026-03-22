import hashlib
import json
from pathlib import Path
from typing import Any, Dict


def hash_file(path: Path) -> str:
    """Compute SHA256 hash of a file."""
    sha = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(8192):
            sha.update(chunk)
    return sha.hexdigest()


def create_manifest(artifacts: Dict[str, Dict[str, Any]], output_path: Path) -> None:
    """Write the RUN_LEDGER manifest to disk."""
    with open(output_path, "w") as f:
        json.dump(artifacts, f, indent=2, sort_keys=True)
