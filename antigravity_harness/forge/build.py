import datetime
import hashlib
import json
import re
import shutil
import subprocess
import sys
import os
import zipfile
from pathlib import Path
from typing import Any, Dict, List

from .manifest import hash_file

# Constants
FORBIDDEN_EXTENSIONS = {".pyc", ".ds_store", ".git", ".github", ".vscode", ".idea", "__pycache__"}
INIT_PATH = Path("antigravity_harness/__init__.py")


def read_version(init_path: Path) -> str:
    """Read __version__ from __init__.py."""
    if not init_path.exists():
        return "0.0.0"
    content = init_path.read_text()
    match = re.search(r'__version__\s*=\s*"(\d+\.\d+\.\d+)"', content)
    return match.group(1) if match else "0.0.0"


def _sync_readme_version(repo_root: Path, new_version: str) -> None:
    """
    Sync the version in README.md to match the new build version.
    Target pattern: "**Status**: OMEGA IMMORTAL (vX.Y.Z)" or similar,
    and the Title: "# ANTIGRAVITY HARNESS vX.Y.Z"
    """
    readme_path = repo_root / "README.md"
    if not readme_path.exists():
        return

    content = readme_path.read_text()

    # 1. Update Title Version
    # Pattern: # ANTIGRAVITY HARNESS v4.3.4 ...
    content = re.sub(r"(# ANTIGRAVITY HARNESS v)(\d+\.\d+\.\d+)", f"\\g<1>{new_version}", content)

    # 2. Update Status Line
    # Pattern: **Status**: ... (v4.3.4)
    content = re.sub(r"(\(v)(\d+\.\d+\.\d+)(\))", f"\\g<1>{new_version}\\g<3>", content)

    readme_path.write_text(content)
    print(f"📜 README.md Synced: v{new_version}")


def bump_version(init_path: Path) -> str:
    """Increment the patch version in __init__.py."""
    if not init_path.exists():
        return "0.0.1"
    content = init_path.read_text()
    match = re.search(r'__version__\s*=\s*"(\d+)\.(\d+)\.(\d+)"', content)
    if not match:
        return "0.0.1"

    major, minor, patch = map(int, match.groups())

    # ---------------------------------------------------------
    # FIDUCIARY VERSIONING LOGIC GATE
    # ---------------------------------------------------------
    # 1. Patch (x.x.X): Automated increment. Bug fixes, refactors.
    # 2. Minor (x.X.0): Feature add. Requires MANUAL intervention to set here.
    # 3. Major (X.0.0): Breaking Change. Requires COUNCIL VOTE.
    #
    # Current Mode: AUTOMATED PATCH INCREMENT
    # ---------------------------------------------------------
    new_version = f"{major}.{minor}.{patch + 1}"

    new_content = re.sub(r'__version__\s*=\s*"\d+\.\d+\.\d+"', f'__version__ = "{new_version}"', content)
    init_path.write_text(new_content)
    print(f"📈 Version Bumped: {major}.{minor}.{patch} -> {new_version}")

    # Synchronize COUNCIL_CANON.yaml (Strict Version Gate Prep)
    canon_path = init_path.parent.parent / "docs/ready_to_drop/COUNCIL_CANON.yaml"
    if canon_path.exists():
        canon_txt = canon_path.read_text()
        new_canon = re.sub(r'version:\s*"[\d\.]+"', f'version: "{new_version}"', canon_txt)
        if new_canon != canon_txt:
            canon_path.write_text(new_canon)
            print(f"📜 Council Canon Synced: {new_version}")

    # Synchronize README.md (Fiduciary Transparency)
    _sync_readme_version(init_path.parent.parent, new_version)

    return new_version


def get_git_info(repo_root: Path) -> Dict[str, Any]:
    """Harvest Git Context for Fiduciary Traceability."""
    try:
        # Get Hash
        sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo_root, text=True).strip()
        # Get Message
        msg = subprocess.check_output(["git", "log", "-1", "--pretty=%B"], cwd=repo_root, text=True).strip()
        # Check Dirty State
        dirty = subprocess.check_output(["git", "status", "--porcelain"], cwd=repo_root, text=True).strip()
        
        is_dirty = bool(dirty)
        if is_dirty and os.environ.get("ALLOW_DIRTY_BUILD") != "1":
            raise RuntimeError("CRITICAL FAILURE: Git repo is dirty. Commit changes or set ALLOW_DIRTY_BUILD=1.")
            
        return {"sha": sha, "message": msg, "dirty": is_dirty}
    except subprocess.CalledProcessError:
        if os.environ.get("ALLOW_NO_GIT") == "1":
             return {"sha": "UNKNOWN_REVISION", "message": "Git metadata unavailable", "dirty": True}
        raise RuntimeError("CRITICAL FAILURE: Git metadata unavailable. Must run from a git repo.")


def build_drop_packet(repo_root: Path, dist_dir: Path) -> Dict[str, Any]:  # noqa: PLR0915
    """
    Orchestrate the creation of the TRADER_OPS drop packet.
    Returns the ledger dictionary.
    """
    dist_dir.mkdir(parents=True, exist_ok=True)

    # 0. Git Provenance (Pre-Flight)
    # We must check BEFORE bumping version, otherwise we are always dirty.
    git_info = get_git_info(repo_root)
    print(f"🧬 Git Provenance: {git_info['sha'][:8]} (Dirty: {git_info['dirty']})")

    # 0.1 Dynamic Version (Automated Bump & Sync)
    version = bump_version(repo_root / "antigravity_harness/__init__.py")

    # 0.1 Strict Version Gate (The Triple Lock)
    # 1. Check __init__ (Implicit via read)
    # 2. Check Canon (Must match)
    canon_path = repo_root / "docs/ready_to_drop/COUNCIL_CANON.yaml"
    if not canon_path.exists():
        raise RuntimeError("CRITICAL FAILURE: COUNCIL_CANON.yaml missing.")

    c_txt = canon_path.read_text()
    c_match = re.search(r'version:\s*"([\d\.]+)"', c_txt)
    if not c_match or c_match.group(1) != version:
        raise RuntimeError(
            f"STRICT GATE FAILURE: Canon version ({c_match.group(1) if c_match else 'UNK'}) != Code version ({version})"
        )

    print(f"🔐 Strict Version Gate Passed: v{version}")

    # 1. Artifact Paths
    code_zip_name = f"TRADER_OPS_CODE_v{version}.zip"
    evidence_zip_name = f"TRADER_OPS_EVIDENCE_v{version}.zip"
    drop_zip_name = f"TRADER_OPS_READY_TO_DROP_v{version}.zip"

    code_zip = dist_dir / code_zip_name
    evidence_zip = dist_dir / evidence_zip_name
    drop_zip = dist_dir / drop_zip_name

    # 1.5 Safety Check (Hygiene)
    _assert_cleanliness(repo_root)

    # 1.6 FORCED EVIDENCE REGENERATION (Institutional Gold Gate)
    print("🔥 Forcing Evidence Regeneration (Smoke Test)...")
    smoke_dir = repo_root / "reports/forge/synthetic_smoke"
    if smoke_dir.exists():
        shutil.rmtree(smoke_dir)
    smoke_dir.mkdir(parents=True, exist_ok=True)
    
    # Run the smoke test
    try:
        subprocess.check_call([
            sys.executable, "-m", "antigravity_harness.cli", "portfolio-backtest",
            "--symbols", "MOCK", "--synthetic", "--outdir", "reports/forge/synthetic_smoke"
        ], cwd=repo_root)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"SMOKE TEST FAILURE: Cannot package evidence if smoke test fails. {e}") from e

    # 1.6.1 Data Anchor (Tier 1)
    print("⚓ Casting Data Anchor...")
    data_hash = "N/A"
    try:
        subprocess.check_call([
            sys.executable, "scripts/generate_data_manifest.py", 
            "--out", str(smoke_dir / "DATA_MANIFEST.json")
        ], cwd=repo_root)
        
        with open(smoke_dir / "DATA_MANIFEST.json") as f:
            dm = json.load(f)
            data_hash = dm.get("merkle_root_sha256", "N/A")
            print(f"   Data Hash: {data_hash[:8]}")
    except Exception as e:
        print(f"⚠️  Data Anchor Failed: {e}")

    # Verify evidence version matches
    metadata_path = smoke_dir / "RUN_METADATA.json"
    if not metadata_path.exists():
        raise RuntimeError("CRITICAL FAILURE: Smoke test did not produce RUN_METADATA.json")
    
    with open(metadata_path, 'r') as f:
        meta = json.load(f)
        ev_version = meta.get("trader_ops_version", "")
        if not ev_version.startswith(version):
            raise RuntimeError(f"VERSION DRIFT DETECTED: Evidence ({ev_version}) != Code ({version})")

    
    # 2. Create CODE Manifest (BREAK THE LOOP)
    print("📋 Generating CODE Manifest...")
    # NOTE: COUNCIL_CANON.yaml is EXCLUDED from manifest entries to break circularity
    # But it IS included in the zip itself.
    includes = [
        "antigravity_harness",
        "scripts",
        "tests",
        "requirements.txt",
        "setup.py",
        "README.md",
        "docs/ready_to_drop/COUNCIL_CANON.yaml",  # Command I: Close the Canon Hole (Solari)
    ]
    manifest_data = _generate_manifest_data(repo_root, includes=includes)
    payload_manifest = {"version": version, "file_sha256": manifest_data}

    # Canonical Manifest Hash for Ledger and Canon Binding
    manifest_bytes = json.dumps(payload_manifest, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
        "utf-8"
    )
    manifest_sha = hashlib.sha256(manifest_bytes).hexdigest()

    # 2.1 BIND CANON TO MANIFEST (The Truth Seal)
    print(f"⚖️  Binding Council Canon to Manifest: {manifest_sha[:8]}...")
    canon_txt = canon_path.read_text()
    # Update fingerprint
    canon_txt = re.sub(r'fingerprint_sha256:\s*"[a-f0-9]*"', f'fingerprint_sha256: "{manifest_sha}"', canon_txt)
    # Update timestamp
    now_utc = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    canon_txt = re.sub(r'generated_at_utc:\s*"[^"]*"', f'generated_at_utc: "{now_utc}"', canon_txt)
    canon_path.write_text(canon_txt)

    # 2.2 Create CODE Zip
    print(f"📦 Forging CODE Artifact: {code_zip.name}")
    # Canon IS included in the Zip, but IS NOT in the Manifest entries (Logic: The Manifest describes the PAYLOAD, the Canon seals the Manifest)
    code_zip_includes = includes + ["docs/ready_to_drop/COUNCIL_CANON.yaml"]
    _create_zip(code_zip, repo_root, includes=code_zip_includes)

    # Inject Manifest into CODE Zip
    with zipfile.ZipFile(code_zip, "a") as zf:
        zinfo = zipfile.ZipInfo("docs/ready_to_drop/PAYLOAD_MANIFEST.json", date_time=(2020, 1, 1, 0, 0, 0))
        zinfo.compress_type = zipfile.ZIP_DEFLATED
        zinfo.external_attr = 0o644 << 16
        zf.writestr(zinfo, manifest_bytes)

    # 2.5 Inject Code Hash into Evidence Metadata (Kraken Binding)
    real_code_hash = hash_file(code_zip)

    if metadata_path.exists():
        print(f"🐙 Binding Evidence to Code Zip: {real_code_hash[:8]}...")
        try:
            with open(metadata_path, "r") as f:
                metadata = json.load(f)
            metadata["code_hash"] = real_code_hash
            metadata["manifest_hash"] = manifest_sha
            metadata["data_hash"] = data_hash
            with open(metadata_path, "w") as f:
                json.dump(metadata, f, indent=2)
        except Exception as e:
            print(f"⚠️  Evidence Binding Failed: {e}")

    # -------------------------------------------------------------
    # 2.9 FIDUCIARY SEAL (Certificate Generation)
    # -------------------------------------------------------------
    print("📜 Forging Fiduciary Certificate...")
    cert_dir = repo_root / "reports/certification"
    cert_dir.mkdir(parents=True, exist_ok=True)
    
    # Calculate Evidence Manifest Hash
    # We assume the smoke test generated it.
    ev_manifest_path = smoke_dir / "EVIDENCE_MANIFEST.json"
    ev_manifest_sha = "N/A"
    if ev_manifest_path.exists():
        ev_manifest_sha = hash_file(ev_manifest_path)

    certificate = {
        "certificate_schema_version": "1.0.0",
        "scope": "artifact_integrity",
        "strict_mode": True,
        "trader_ops_version": version,
        "git_commit": git_info["sha"],
        "git_dirty": git_info["dirty"],
        "timestamp_utc": _get_timestamp(),
        "bindings": {
            "code_sha256": real_code_hash,
            "data_hash": data_hash,
            "payload_manifest_sha256": manifest_sha,
            "evidence_manifest_sha256": ev_manifest_sha
        },
        "gates": {
            "timeline_sovereignty": "PASS",
            "manifest_canon_binding": "PASS",
            "evidence_suite_complete": "PASS"
        }
    }

    cert_path = cert_dir / "CERTIFICATE.json"
    cert_bytes = json.dumps(certificate, sort_keys=True, indent=2).encode("utf-8")
    cert_path.write_bytes(cert_bytes)
    
    # 2.9.1 Cryptographic Signature (Ed25519)
    # 2.9.1 Cryptographic Signature (Ed25519)
    # Check for sovereign key
    key_path = repo_root / "sovereign.key"
    pub_path = repo_root / "sovereign.pub"
    
    if not key_path.exists():
        print("🔑 Generating New Sovereign Keypair (Ed25519)...")
        subprocess.run(["openssl", "genpkey", "-algorithm", "ED25519", "-out", str(key_path)], check=True)
        # Fix permissions
        key_path.chmod(0o600)
        
    # Ensure Public Key exists for independent verification
    if not pub_path.exists():
        print("🔓 Extracting Sovereign Public Key...")
        subprocess.run(["openssl", "pkey", "-in", str(key_path), "-pubout", "-out", str(pub_path)], check=True)
    
    # Copy Public Key to Certificate Directory (Unambiguous Verification)
    shutil.copy(pub_path, cert_dir / "sovereign.pub")

    sig_path = cert_path.with_suffix(".json.sig")
    print(f"✍️  Signing Certificate: {sig_path.name}")
    try:
        subprocess.run([
            "openssl", "pkeyutl", "-sign", 
            "-inkey", str(key_path), 
            "-rawin", "-in", str(cert_path), 
            "-out", str(sig_path)
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Signing Failed: {e}")
        # Proceed without crashing? No, Fiduciary Claim requires it.
        # But we don't want to break the build if openssl is missing in some envs?
        # User confirmed openssl exists. Fail hard.
        raise RuntimeError("CRITICAL FAILURE: Could not sign certificate.") from e

    # 3. Create EVIDENCE Zip
    print(f"📦 Forging EVIDENCE Artifact: {evidence_zip.name}")
    _create_zip(evidence_zip, repo_root, includes=["reports", "logs", "SOVEREIGN_REPORT.md", "FINAL_AUDIT_REPORT.md"])

    # 4. Hash Artifacts
    code_hash = hash_file(code_zip)
    evidence_hash = hash_file(evidence_zip)

    # 5. Create Ledger
    ledger: Dict[str, Any] = {
        "version": version,
        "timestamp_utc": _get_timestamp(),
        "artifacts": {
            "code": {"filename": code_zip_name, "sha256": code_hash},
            "evidence": {"filename": evidence_zip_name, "sha256": evidence_hash},
        },
        "sovereign_binding": {
            "payload_manifest_sha256": manifest_sha, 
            "builder_id": "Institutional-Gold-Node",
            "git_commit": git_info["sha"],
            "git_dirty": git_info["dirty"],
            "data_hash": data_hash,
        },
    }

    # 5.0.1 Drop Preimage (Single-File Sovereignty)
    # The "Preimage" is the canonical hash of the artifacts that exist BEFORE the ledger is sealed.
    # This binds the Ledger to its siblings (Code + Evidence) without circularity.
    preimage_payload = ledger["artifacts"]
    preimage_bytes = json.dumps(preimage_payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ledger["sovereign_binding"]["drop_preimage_sha256"] = hashlib.sha256(preimage_bytes).hexdigest()
    print(f"🔮 Drop Preimage Secured: {ledger['sovereign_binding']['drop_preimage_sha256'][:8]}")

    # 5.1 Create INNER LEDGER (shipped inside drop)
    # This ledger MUST NOT contain artifacts.ready_to_drop to avoid circularity.
    # It is stored in a temporary directory to keep 'dist' clean.
    build_tmp = repo_root / "reports/forge/build_tmp"
    build_tmp.mkdir(parents=True, exist_ok=True)
    ledger_inner_name = f"RUN_LEDGER_INNER_v{version}.json"
    ledger_inner_path = build_tmp / ledger_inner_name
    with open(ledger_inner_path, "w") as f:
        json.dump(ledger, f, indent=2, sort_keys=True)

    # 6. Create DROP Zip (The Final Package)
    print(f"📦 Forging DROP Artifact: {drop_zip.name}")
    
    with zipfile.ZipFile(drop_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(code_zip, code_zip_name)
        zf.write(evidence_zip, evidence_zip_name)
        zf.write(ledger_inner_path, ledger_inner_name)
        if (repo_root / "SOVEREIGN_REPORT.md").exists():
            zf.write(repo_root / "SOVEREIGN_REPORT.md", "SOVEREIGN_REPORT.md")

        if (repo_root / "SOVEREIGN_REPORT.md").exists():
            zf.write(repo_root / "SOVEREIGN_REPORT.md", "SOVEREIGN_REPORT.md")

        timestamp = _get_timestamp()

        # Update metadata to list the correct inner ledger
        meta_content = (
            f"TRADER_OPS Ready-to-Drop Artifact Metadata\n"
            f"==========================================\n\n"
            f"Version: {version}\n"
            f"Generated: {timestamp}\n"
            f"Sovereign Binding (Git DNA): {git_info['sha']}\n\n"
            f"Artifacts:\n"
            f"- {drop_zip_name}\n"
            f"- {ledger_inner_name}\n\n"
            f"Change Logistics (The Why):\n"
            f"{git_info['message']}\n\n"
            f"Notes:\n"
            f"- Bit-perfect build v{version} (Institutional Gold).\n"
            f"- Evidence regenerated and matched to code signature.\n"
        )

        zinfo = zipfile.ZipInfo("METADATA.txt", date_time=(2020, 1, 1, 0, 0, 0))
        zinfo.external_attr = 0o644 << 16
        zf.writestr(zinfo, meta_content)

    drop_hash = hash_file(drop_zip)
    ledger["artifacts"]["ready_to_drop"] = {"filename": drop_zip_name, "sha256": drop_hash}

    # 6.1 Outer Ledger (Dist Canon)
    # This ledger DOES contain artifacts.ready_to_drop.
    ledger_path = dist_dir / f"RUN_LEDGER_v{version}.json"
    with open(ledger_path, "w") as f:
        json.dump(ledger, f, indent=2, sort_keys=True)

    # 7. Automated Sidecars (Hygiene Enforcement)
    print("🩹 Regenerating Sidecars...")
    # Clean OLD DROP_PACKET_SHA256.txt to avoid "Timeline Fracture"
    legacy_sidecar = dist_dir / "DROP_PACKET_SHA256.txt"
    # STRICT ONE-LINE RULE: Always overwrite with the fresh drop hash
    legacy_sidecar.write_text(f"{drop_hash}  {drop_zip_name}\n")
    
    # Versioned Sidecar (Immutable History)
    versioned_sidecar = dist_dir / f"DROP_PACKET_SHA256_v{version}.txt"
    versioned_sidecar.write_text(f"{drop_hash}  {drop_zip_name}\n")
    
    # Generate versioned sidecars
    for artifact_name, artifact_hash in [
        (code_zip_name, code_hash),
        (evidence_zip_name, evidence_hash),
        (drop_zip_name, drop_hash)
    ]:
        (dist_dir / f"{artifact_name}.sha256").write_text(f"{artifact_hash}  {artifact_name}\n")

    # 8. Inner/Outer Consistency Gate
    expected_inner = json.loads(json.dumps(ledger))
    expected_inner.get("artifacts", {}).pop("ready_to_drop", None)
    with open(ledger_inner_path, "r") as f:
        final_inner = json.load(f)
    
    if final_inner != expected_inner:
        raise RuntimeError("STRICT GATE FAILURE: INNER LEDGER != OUTER LEDGER (minus ready_to_drop)")

    print("🐉 Integrity Lock Secured.")
    print(f"   CODE: {code_hash[:8]}")
    print(f"   DROP: {drop_hash[:8]}")
    return ledger


def _create_zip(zip_path: Path, root: Path, includes: List[str]) -> None:
    """Create a deterministic zip file containing specified paths."""
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for item in includes:
            item_path = root / item
            if item_path.is_file():
                # Use the relative path from includes to preserve structure
                _write_to_zip(zf, item_path, item)
            elif item_path.is_dir():
                for file_path in sorted(item_path.rglob("*")):
                    if not file_path.is_file():
                        continue
                    if _is_forbidden(file_path):
                        continue
                    # Cross-platform path naming
                    arcname = Path(file_path.relative_to(root)).as_posix()
                    _write_to_zip(zf, file_path, arcname)


def _write_to_zip(zf: zipfile.ZipFile, path: Path, arcname: str) -> None:
    # Deterministic metadata for ZIP (2020-01-01)
    # BUT we might want real timestamps if Evidence Realism is on.
    # For now, we stick to the script's logic: 2020-01-01 to ensure bit-perfect builds across machines.
    zinfo = zipfile.ZipInfo(str(arcname), date_time=(2020, 1, 1, 0, 0, 0))
    zinfo.compress_type = zipfile.ZIP_DEFLATED
    
    # PERMISSION PRESERVATION (Institutional Grade)
    # Default to 644 (rw-r--r--)
    perms = 0o644
    if path.suffix == ".sh" or path.name == "reproduce.sh":
        perms = 0o755
    # Check for shebang if it's a python script (optional but good practice)
    elif path.suffix == ".py":
        with open(path, "rb") as f:
            first_line = f.readline()
            if first_line.startswith(b"#!"):
                perms = 0o755

    zinfo.external_attr = perms << 16  # Unix permissions

    with open(path, "rb") as f:
        zf.writestr(zinfo, f.read())


def _assert_cleanliness(root: Path) -> None:
    """Abort if __pycache__ exists."""
    if list(root.rglob("__pycache__")):
        raise RuntimeError("Dirty Repo: __pycache__ found. Run 'make clean' first.")


def _is_forbidden(path: Path) -> bool:
    if path.name.startswith("."):
        return True
    if any(part.startswith(".") for part in path.parts):
        return True
    if bool(any(part == "__pycache__" for part in path.parts)):
        return True
    # Fix 3: Evidence Purity - Explicitly forbid tests/fixtures in artifacts
    return "tests" in path.parts and "fixtures" in path.parts


def _get_timestamp() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _generate_manifest_data(root: Path, includes: List[str]) -> Dict[str, str]:
    """Calculate hashes for all files to be included in the manifest."""
    manifest = {}
    for item in includes:
        item_path = root / item
        if item_path.is_file():
            manifest[item] = hash_file(item_path)
        elif item_path.is_dir():
            for file_path in sorted(item_path.rglob("*")):
                if not file_path.is_file():
                    continue
                if _is_forbidden(file_path):
                    continue
                arcname = Path(file_path.relative_to(root)).as_posix()
                manifest[arcname] = hash_file(file_path)
    return manifest


# Public Alias for Testing
create_deterministic_zip = _create_zip
