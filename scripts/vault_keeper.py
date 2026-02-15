#!/usr/bin/env python3
"""
THE VAULT KEEPER (Iron Bank Protocol)
-------------------------------------
Promotes Sovereign Artifacts from the ephemeral `dist/` forge
to the permanent `vault/` storage.

Motto: "Transit Integrity is Non-Negotiable."
"""

import contextlib
import hashlib
import json
import os
import re
import shutil
import sys
from pathlib import Path
from typing import Optional

DIST_DIR = Path("dist")
VAULT_DIR = Path("vault")


def get_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def version_key(path: Path):
    return [int(x) for x in re.findall(r"\d+", path.name)]


class VaultKeeper:
    def __init__(self, dist: Path, vault: Path):
        self.dist = dist
        self.vault = vault
        self.green = "\033[92m"
        self.red = "\033[91m"
        self.reset = "\033[0m"

    def find_latest_drop(self) -> Optional[Path]:
        drops = sorted(list(self.dist.glob("TRADER_OPS_READY_TO_DROP_v*.zip")), key=version_key)
        return drops[-1] if drops else None

    def get_version_from_filename(self, path: Path) -> str:
        # TRADER_OPS_READY_TO_DROP_v4.4.12.zip -> 4.4.12
        match = re.search(r"v(\d+\.\d+\.\d+)", path.name)
        if not match:
            raise ValueError(f"Filename {path.name} does not contain version pattern.")
        return match.group(1)

    def promote(self):
        print("🏦 VAULT KEEPER: INITIALIZED")

        # 1. Acquire Artifact
        drop_zip = self.find_latest_drop()
        if not drop_zip:
            print(f"{self.red}❌ No Drop Packet found in {self.dist}{self.reset}")
            sys.exit(1)

        version = self.get_version_from_filename(drop_zip)
        print(f"📦 Acquiring Target: {drop_zip.name} (v{version})")

        # 2. Prepare Vault Cell
        cell_dir = self.vault / f"v{version}"
        if cell_dir.exists():
            print(f"⚠️  Vault Cell v{version} already exists. Overwriting (Fiduciary Re-Issue).")
            shutil.rmtree(cell_dir)
        cell_dir.mkdir(parents=True, exist_ok=True)

        # 3. Identify Convoy (All related artifacts for this version)
        # We want: Drop Zip, Ledger, Sidecar.

        ledger = self.dist / f"RUN_LEDGER_v{version}.json"
        sidecar = self.dist / "DROP_PACKET_SHA256.txt"

        convoy = [drop_zip]
        if ledger.exists():
            convoy.append(ledger)
        if sidecar.exists():
            convoy.append(sidecar)

        # 4. Transit & Integrity Check
        for artifact in convoy:
            print(f"🚚 Transporting: {artifact.name}...", end=" ")
            source_hash = get_sha256(artifact)

            dest_path = cell_dir / artifact.name
            shutil.copy2(artifact, dest_path)

            dest_hash = get_sha256(dest_path)

            if source_hash != dest_hash:
                print(f"{self.red}FAILED{self.reset}")
                print(f"❌ TRANSIT CORRUPTION: {artifact.name}")
                print(f"   Source: {source_hash}")
                print(f"   Dest:   {dest_hash}")
                sys.exit(1)

            print(f"{self.green}SECURE{self.reset}")

        # 5. Update Pointer
        latest_link = self.vault / "LATEST"
        # On some systems symlinks are tricky, so we'll use a text pointer for max compatibility
        # But a symlink is "Standard". Let's try symlink, fallback to text?
        # User asked for "latest versions... saved". A directory symlink is best for navigation.

        try:
            if latest_link.is_symlink() or latest_link.exists():
                latest_link.unlink()
            latest_link.symlink_to(f"v{version}")
            print(f"🔗 Semantic Pointer Updated: LATEST -> v{version}")
        except Exception as e:
            print(f"⚠️  Symlink failed ({e}). Creating LATEST.txt pointer.")
            (self.vault / "LATEST.txt").write_text(f"v{version}")

        print(f"\n{self.green}✅ Vault Transaction Complete. v{version} Secured.{self.reset}")


class SecretsVault:
    """
    Fiduciary Secrets Management.
    Provides a standardized way to retrieve API keys without hardcoding.
    """

    def __init__(self, secrets_path: Path):
        self.path = secrets_path

    def get_secret(self, key: str) -> Optional[str]:
        """Retrieve a secret from the vault."""
        if not self.path.exists():
            return None

        try:
            secrets = json.loads(self.path.read_text())
            return secrets.get(key)
        except Exception:
            return None

    def store_secret(self, key: str, val: str):
        """Store a secret (Standard KV overwrites)."""
        secrets = {}
        if self.path.exists():
            with contextlib.suppress(Exception):
                secrets = json.loads(self.path.read_text())
        secrets[key] = val
        self.path.write_text(json.dumps(secrets, indent=4))
        # Ensure strict permissions
        os.chmod(self.path, 0o600)


if __name__ == "__main__":
    keeper = VaultKeeper(DIST_DIR, VAULT_DIR)
    # The promote call is strictly for artifacts.
    # SecretsVault is for live credentials (out-of-band).
    keeper.promote()
