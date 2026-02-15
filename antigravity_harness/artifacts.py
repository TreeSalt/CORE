import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Set

import numpy as np
import pandas as pd


class ArtifactManager:
    """
    The Warden of I/O.
    Ensures all file writes are tracked, hashed, and authorized.
    """

    def __init__(self, root_dir: Path):
        self.root_dir = root_dir.resolve()
        self.registry: Dict[str, str] = {}  # relative_path -> sha256
        self.active_paths: Set[str] = set()

    def get_abs_path(self, relative_path: str) -> Path:
        """Resolve a relative path against the secure root."""
        full_path = (self.root_dir / relative_path).resolve()
        if not str(full_path).startswith(str(self.root_dir)):
            raise PermissionError(f"Path Traversal Detected: {relative_path}")
        full_path.parent.mkdir(parents=True, exist_ok=True)
        return full_path

    def write_text(self, relative_path: str, content: str, overwrite: bool = False) -> None:
        """Write text content and immediately register the artifact. (Atomic)"""
        path = self.get_abs_path(relative_path)
        if path.exists() and not overwrite:
            raise FileExistsError(f"Artifact Sovereignty: Cannot overwrite {relative_path}")
        
        # HYDRA GUARD: Atomic Write Enforcement (Vector 42)
        tmp_path = path.with_suffix(path.suffix + ".tmp")
        tmp_path.write_text(content, encoding="utf-8")
        # Ensure bits hit the disk
        with open(tmp_path, "a") as f:
            f.flush()
            os.fsync(f.fileno())
        
        os.replace(tmp_path, path)
        self._register(path, relative_path)

    def write_json(self, relative_path: str, data: Any, overwrite: bool = False) -> None:
        """Write JSON content canonically and register."""

        def sovereign_encoder(obj: Any) -> Any:  # noqa: PLR0911
            if isinstance(obj, (pd.Timestamp, pd.DatetimeIndex)):
                return str(obj)
            if isinstance(obj, pd.DataFrame):
                return obj.to_dict(orient="records")
            if isinstance(obj, (np.int64, np.integer)):
                return int(obj)
            if isinstance(obj, (np.float64, np.floating)):
                return float(obj)
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            if hasattr(obj, "model_dump"):
                return obj.model_dump()
            return str(obj)

        content = json.dumps(data, indent=2, sort_keys=True, default=sovereign_encoder)
        self.write_text(relative_path, content, overwrite=overwrite)

    def _register(self, path: Path, relative_path: str) -> None:
        """Compute SHA256 and register."""
        sha = hashlib.sha256(path.read_bytes()).hexdigest()
        self.registry[relative_path] = sha
        print(f"🛡️  Artifact Secured: {relative_path} ({sha[:8]})")

    def generate_receipt(self) -> Dict[str, str]:
        """Return the session ledger."""
        return self.registry.copy()
