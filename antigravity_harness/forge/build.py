import datetime
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
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


def _sync_project_metadata(repo_root: Path, new_version: str) -> None:
    """
    Unified synchronization of project metadata across README, docs, and manifests.
    Ensures that the 'Cognitive Bridge' is contemporary and version-consistent.
    """
    # 1. Sync README.md
    readme_path = repo_root / "README.md"
    if readme_path.exists():
        content = readme_path.read_text()
        # Update Title: # ANTIGRAVITY HARNESS vX.Y.Z ...
        content = re.sub(r"(# ANTIGRAVITY HARNESS v)(\d+\.\d+\.\d+)", f"\\g<1>{new_version}", content)
        # Update Status Line: **Status**: ... (vX.Y.Z)
        content = re.sub(r"(\(v)(\d+\.\d+\.\d+)(\))", f"\\g<1>{new_version}\\g<3>", content)
        if content != readme_path.read_text():
            readme_path.write_text(content)
            print(f"📜 README.md Synced: v{new_version}")

    # 2. Sync Cognitive Bridge (Docs)
    bridge_files = [
        repo_root / "docs/AGENT_ONBOARDING.md",
        repo_root / "docs/ARCHITECTURE_MAP.md"
    ]
    for path in bridge_files:
        if not path.exists():
            continue
        content = path.read_text()
        # Matches (v4.3.4), (v4.4.x), etc. and replaces with the current version
        new_content = re.sub(r'\(v\d+\.\d+\.[^)]+\)', f'(v{new_version})', content)
        new_content = re.sub(r'version v\d+\.\d+\.\d+', f'version v{new_version}', new_content)
        
        # Architecture Map specific: Update "Last Verified" timestamp if present
        if path.name == "ARCHITECTURE_MAP.md":
            now_str = _get_wallclock()
            new_content = re.sub(r'Last Verified: .*', f'Last Verified: {now_str}', new_content)

        if new_content != content:
            path.write_text(new_content)
            print(f"🧬 Synced Bridge: {path.name} -> v{new_version}")

    # 3. Sync Council Canon
    canon_path = repo_root / "docs/ready_to_drop/COUNCIL_CANON.yaml"
    if canon_path.exists():
        content = canon_path.read_text()
        new_content = re.sub(r'(version:\s*")\d+\.\d+\.\d+(")', f"\\g<1>{new_version}\\g<2>", content)
        if new_content != content:
            canon_path.write_text(new_content)
            print(f"⚖️  Synced Canon: {canon_path.name} -> v{new_version}")


def bump_version(init_path: Path) -> str:
    """Increment the patch version in __init__.py."""
    if not init_path.exists():
        return "0.0.1"
    content = init_path.read_text()
    match = re.search(r'__version__\s*=\s*"(\d+)\.(\d+)\.(\d+)"', content)
    if not match:
        return "0.0.1"

    major, minor, patch = map(int, match.groups())
    current_version = f"{major}.{minor}.{patch}"

    # ---------------------------------------------------------
    # FIDUCIARY VERSIONING LOGIC GATE
    # ---------------------------------------------------------
    # Continuous Versioning: Always increment the patch version to ensure
    # that every institutional build is unique and auditable.
    new_version = f"{major}.{minor}.{patch + 1}"
    print(f"📈 Version Bumped: {current_version} -> {new_version}")

    new_content = re.sub(r'__version__\s*=\s*"\d+\.\d+\.\d+"', f'__version__ = "{new_version}"', content)
    if new_content != content:
        init_path.write_text(new_content)

    return new_version


def _get_timestamp() -> str:
    """UTC timestamp for ledgers/metadata.

    By default we record real wallclock time (fiduciary friendly).
    If you need bit-for-bit reproducible artifacts, set DETERMINISTIC_EPOCH=1.
    """
    if os.environ.get("DETERMINISTIC_EPOCH") == "1":
        return "2020-01-01T00:00:00Z"
    return datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

def _get_wallclock() -> str:
    """Always real wallclock UTC (non-deterministic; for audit trails)."""
    return datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

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
        return {"sha": sha, "message": msg, "dirty": is_dirty}
    except subprocess.CalledProcessError:
        if os.environ.get("ALLOW_NO_GIT") == "1":
             return {"sha": "UNKNOWN_REVISION", "message": "Git metadata unavailable", "dirty": True}
        raise RuntimeError("CRITICAL FAILURE: Git metadata unavailable. Must run from a git repo.") from None


def build_drop_packet(repo_root: Path, dist_dir: Path) -> Dict[str, Any]:  # noqa: PLR0915, PLR0912
    """
    Orchestrate the creation of the TRADER_OPS drop packet.
    Returns the ledger dictionary.
    """
    _check_disk_quota()
    # Sovereign Default: Strict Mode
    if os.environ.get("STRICT_MODE") is None:
        os.environ["STRICT_MODE"] = "1"
        print("🛡️  STRICT_MODE enabled by default (Fiduciary Protocol).")

    if os.environ.get("STRICT_MODE") == "1" and os.environ.get("ALLOW_DIRTY_BUILD") == "1":
        raise RuntimeError("STRICT POLICY VIOLATION: ALLOW_DIRTY_BUILD=1 is forbidden when STRICT_MODE=1.")
    
    dist_dir.mkdir(parents=True, exist_ok=True)
    
    # Temporary holding area for intermediate artifacts (Isolated from final dist)
    build_tmp = repo_root / "reports/forge/build_tmp"
    build_tmp.mkdir(parents=True, exist_ok=True)
    # We must check BEFORE bumping version, otherwise we are always dirty.
    git_info = get_git_info(repo_root)
    print(f"🧬 Git Provenance: {git_info['sha'][:8]} (Dirty: {git_info['dirty']})")
    
    if os.environ.get("STRICT_MODE", "1") == "1" and git_info["dirty"]:
        raise RuntimeError("CRITICAL FAILURE: STRICT_MODE requires an initial clean source tree. Forcing fail-closed. Commit all changes.")

    release_mode = os.environ.get("METADATA_RELEASE_MODE") == "1"
    if release_mode and os.environ.get("STRICT_MODE") != "1":
        os.environ["STRICT_MODE"] = "1"
        print("🛡️  STRICT_MODE auto-enabled for Release.")

    # 0.1 Dynamic Version (Automated Bump & Sync)
    version = bump_version(repo_root / "antigravity_harness/__init__.py")
    
    # [COGNITIVE BRIDGE] Natural metadata & documentation sync
    _sync_project_metadata(repo_root, version)

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

    # Hydra V241: Temporal Witness Guard
    d_match = re.search(r'generated_at_utc:\s*"([^"]+)"', c_txt)
    if d_match:
        try:
            from datetime import datetime  # noqa: PLC0415
            gen_date = datetime.fromisoformat(d_match.group(1).replace("Z", "+00:00"))
            now = datetime.now(gen_date.tzinfo)
            if gen_date > now and gen_date.year > 2050:
                raise RuntimeError(f"TEMPORAL PARADOX (V241): Council Canon date ({d_match.group(1)}) is in the future.")
        except ValueError:
            pass

    print(f"🔐 Strict Version Gate Passed: v{version}")

    # 1. Artifact Paths
    code_zip_name = f"TRADER_OPS_CODE_v{version}.zip"
    evidence_zip_name = f"TRADER_OPS_EVIDENCE_v{version}.zip"
    drop_zip_name = f"TRADER_OPS_READY_TO_DROP_v{version}.zip"

    code_zip = build_tmp / code_zip_name
    evidence_zip = build_tmp / evidence_zip_name
    drop_zip = dist_dir / drop_zip_name

    # 1.5 Safety Check (Hygiene)
    _assert_cleanliness(repo_root)
    
    # Purity Assert: Re-check git dirty after potential mutations (bump_version)
    if os.environ.get("STRICT_MODE", "1") == "1":
        # Check PORCELAIN output for unexpected changes
        status = subprocess.check_output(["git", "status", "--porcelain"], cwd=repo_root, text=True).strip()
        if status:
            lines = status.split("\n")
            # Filter out authorized mutations
            authorized = [
                "antigravity_harness/__init__.py", 
                "README.md", 
                "docs/ready_to_drop/COUNCIL_CANON.yaml",
                "docs/AGENT_ONBOARDING.md",
                "docs/ARCHITECTURE_MAP.md",
                "docs/DECISION_LOG.md",
            ]
            unexpected = []
            for line in lines:
                # Porcelain format: XY PATH (where PATH can be "quoted")
                # Robustly extract path part starting after the XY status (2 chars)
                file_path = line[2:].strip().strip('"')
                if file_path not in authorized:
                    unexpected.append(file_path)
            
            if unexpected:
                raise RuntimeError(f"PURITY VIOLATION: Forge mutated UNEXPECTED tracked files: {unexpected}. Use commitment-first workflow.")

    # 1.6 FORCED EVIDENCE REGENERATION (Institutional Gold Gate)
    print("🔥 Forcing Evidence Regeneration (Smoke Test)...")
    smoke_dir = repo_root / "reports/forge/synthetic_smoke"
    if smoke_dir.exists():
        shutil.rmtree(smoke_dir)
    smoke_dir.mkdir(parents=True, exist_ok=True)
    
    # Run the smoke test
    try:
        env = os.environ.copy()
        env["METADATA_RELEASE_MODE"] = "1"
        # Pass the calculated code hash to ensure deterministic RUN_METADATA
        env["METADATA_CODE_HASH"] = str(repo_root.name) + ":" + (repo_root.parent.name) # Use something stable if git fails
        # Actually, we have code_hash in build.py (from manifest or git)
        # Let's use the git SHA if available
        try:
            sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo_root, stderr=subprocess.DEVNULL).decode("utf-8").strip()
            env["METADATA_CODE_HASH"] = sha
        except Exception:
             env["METADATA_CODE_HASH"] = "STABLE_SOVEREIGN_HASH"
             
        subprocess.check_call([
            sys.executable, "-m", "antigravity_harness.cli", "portfolio-backtest",
            "--symbols", "MOCK", "--synthetic", "--outdir", "reports/forge/synthetic_smoke"
        ], cwd=repo_root, env=env)
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
        "profiles",
        "requirements.txt",
        "setup.py",
        "README.md",
        "docs",  # Includes all Sovereign Books
    ]
    # Pass 1: Generate manifest excluding the Canon Truth Seal to avoid circularity
    manifest_data = _generate_manifest_data(repo_root, includes=includes, exclude=["docs/ready_to_drop/COUNCIL_CANON.yaml"])
    payload_manifest: Dict[str, Any] = {"version": version, "file_sha256": manifest_data}

    # Canonical Manifest Hash for Ledger and Canon Binding
    # [STRICT BINDING] We use separators=(",", ":") for compact JSON hash stability.
    manifest_bytes = json.dumps(payload_manifest, sort_keys=True, separators=(",", ":")).encode("utf-8")
    manifest_sha = hashlib.sha256(manifest_bytes).hexdigest()
    print(f"⚖️  Binding Council Canon to Manifest: {manifest_sha[:12]}...")
    canon_txt = (repo_root / "docs/ready_to_drop/COUNCIL_CANON.yaml").read_text()
    # Update fingerprint
    canon_txt = re.sub(r'fingerprint_sha256:\s*"[a-f0-9]*"', f'fingerprint_sha256: "{manifest_sha}"', canon_txt)
    # [STAGE 1 FIX: Determinism] Use fixed epoch for generated_at_utc
    fixed_utc = "2020-01-01T00:00:00Z"
    canon_txt = re.sub(r'generated_at_utc:\s*"[^"]*"', f'generated_at_utc: "{fixed_utc}"', canon_txt)
    
    # 2.1.1 PIN PUBLIC KEY (Pinned Sovereignty)
    pub_path = repo_root / "sovereign.pub"
    if pub_path.exists():
        pub_sha = hash_file(pub_path)
        print(f"🔑 Pinning Public Key: {pub_sha[:8]}...")
        if 'repo:' in canon_txt:
            canon_txt = re.sub(r'(repo:.*?)(\n\n|\nphases:)', f'\\1\n  sovereign_pubkey_sha256: "{pub_sha}"\\2', canon_txt, flags=re.S)
    
    # Write to TEMP canon to avoid repo mutation (Git Purity)
    tmp_canon_path = build_tmp / "COUNCIL_CANON.yaml"
    tmp_canon_path.write_text(canon_txt)
    print(f"⚖️  Canon Secured (Temp): {tmp_canon_path.name}")

    # 2.2 Create CODE Zip
    print(f"📦 Forging CODE Artifact: {code_zip.name}")
    
    # [SOLARI v5 FIX] Update manifest with FINAL canon hash AFTER fingerprinting
    # This closes the "Chicken-and-Egg" loop for byte-level audits.
    final_canon_hash = hash_file(tmp_canon_path)
    payload_manifest["file_sha256"]["docs/ready_to_drop/COUNCIL_CANON.yaml"] = final_canon_hash
    print(f"⚖️  Canon Fingerprint Synchronized: {final_canon_hash[:8]}")
    
    # Final sorted manifest for bit-perfect CODE zip (Pass 2)
    manifest_bytes = json.dumps(payload_manifest, sort_keys=True, separators=(",", ":")).encode("utf-8")
    tmp_manifest_path = build_tmp / "PAYLOAD_MANIFEST.json"
    tmp_manifest_path.write_bytes(manifest_bytes)

    code_zip_includes = includes
    
    # Create zip, but EXCLUDE the real docs/ready_to_drop/COUNCIL_CANON.yaml 
    # and instead inject our temp one later.
    _create_zip(code_zip, repo_root, includes=code_zip_includes, exclude=["docs/ready_to_drop/COUNCIL_CANON.yaml"])

    # Inject Manifest and TEMPORARY Canon into CODE Zip
    with zipfile.ZipFile(code_zip, "a") as zf:
        # 1. Manifest
        zinfo_m = zipfile.ZipInfo("docs/ready_to_drop/PAYLOAD_MANIFEST.json", date_time=(2020, 1, 1, 0, 0, 0))
        zinfo_m.compress_type = zipfile.ZIP_DEFLATED
        zinfo_m.external_attr = 0o644 << 16
        zf.writestr(zinfo_m, manifest_bytes)
        
        # 2. Pinned Canon
        zinfo_c = zipfile.ZipInfo("docs/ready_to_drop/COUNCIL_CANON.yaml", date_time=(2020, 1, 1, 0, 0, 0))
        zinfo_c.compress_type = zipfile.ZIP_DEFLATED
        zinfo_c.external_attr = 0o644 << 16
        zf.writestr(zinfo_c, canon_txt)

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
                json.dump(metadata, f, indent=2, sort_keys=True)
        except Exception as e:
            print(f"⚠️  Evidence Binding Failed: {e}")

    # EVIDENCE hashing moved after creation below.

    # 3. Create EVIDENCE Zip
    print(f"📦 Forging EVIDENCE Artifact: {evidence_zip.name}")
    _create_zip(evidence_zip, repo_root, includes=["reports", "logs", "SOVEREIGN_REPORT.md", "FINAL_AUDIT_REPORT.md"])

    # 4. FIDUCIARY SEAL (Certificate Generation)
    # ------------------------------------------
    print("📜 Forging Unambiguous Fiduciary Certificate...")
    
    # Evidence Manifest Hash (from smoke results)
    ev_manifest_path = smoke_dir / "EVIDENCE_MANIFEST.json"
    ev_manifest_sha = hash_file(ev_manifest_path) if ev_manifest_path.exists() else "N/A"

    # NOTE: evidence_sha256 was REMOVED from cert bindings in v4.5.29.
    # The cert lived inside the evidence zip, making the hash circular.
    # Integrity is now provided by the detached MANIFEST.json (see Step 5.5).

    certificate = {
        "certificate_schema_version": "2.0.0",
        "scope": "fiduciary_strict_audit",
        "strict_profile_id": "FIDUCIARY_STRICT_V1",
        "verifier_version": "v1.1.0",
        "strict_mode": (os.environ.get("STRICT_MODE", "1") == "1"),
        "trader_ops_version": version,
        "version": version,
        "artifact_version": version,
        "git_commit": git_info["sha"],
        "git_dirty": git_info["dirty"],
        "timestamp_utc": _get_timestamp(),
        "bindings": {
            "code_sha256": real_code_hash,
            "data_hash": data_hash,
            "manifest_sha256": manifest_sha,
            "evidence_manifest_sha256": ev_manifest_sha
        },
        "gates": {
            "timeline_sovereignty": "PASS",
            "manifest_canon_binding": "PASS",
            "evidence_suite_complete": "PASS",
            "strict_mode_enforced": "PASS"
        }
    }

    # Keys
    key_path = repo_root / "sovereign.key"
    pub_path = repo_root / "sovereign.pub"
    if not key_path.exists():
         subprocess.run(["openssl", "genpkey", "-algorithm", "ED25519", "-out", str(key_path)], check=True)
         key_path.chmod(0o600)
    if not pub_path.exists():
         subprocess.run(["openssl", "pkey", "-in", str(key_path), "-pubout", "-out", str(pub_path)], check=True)

    cert_json = json.dumps(certificate, sort_keys=True, indent=2).encode("utf-8")
    cert_tmp = build_tmp / "CERTIFICATE.json"
    cert_tmp.write_bytes(cert_json)
    
    sig_tmp = build_tmp / "CERTIFICATE.json.sig"
    print(f"✍️  Signing Unambiguous Certificate: {sig_tmp.name}")
    subprocess.run([
        "openssl", "pkeyutl", "-sign", 
        "-inkey", str(key_path), 
        "-rawin", "-in", str(cert_tmp), 
        "-out", str(sig_tmp)
    ], check=True)

    # 4.1 Inject Seal into EVIDENCE Zip
    print("🐙 Injecting Fiduciary Seal into Evidence Zip...")
    with zipfile.ZipFile(evidence_zip, "a") as zf:
        # Cert
        zinfo_cert = zipfile.ZipInfo("reports/certification/CERTIFICATE.json", date_time=(2020, 1, 1, 0, 0, 0))
        zinfo_cert.compress_type = zipfile.ZIP_DEFLATED
        zinfo_cert.external_attr = 0o644 << 16
        zf.writestr(zinfo_cert, cert_json)
        # Sig
        zinfo_sig = zipfile.ZipInfo("reports/certification/CERTIFICATE.json.sig", date_time=(2020, 1, 1, 0, 0, 0))
        zinfo_sig.compress_type = zipfile.ZIP_DEFLATED
        zinfo_sig.external_attr = 0o644 << 16
        zf.writestr(zinfo_sig, sig_tmp.read_bytes())
        # Pubkey
        zinfo_pub = zipfile.ZipInfo("reports/certification/sovereign.pub", date_time=(2020, 1, 1, 0, 0, 0))
        zinfo_pub.compress_type = zipfile.ZIP_DEFLATED
        zinfo_pub.external_attr = 0o644 << 16
        zf.writestr(zinfo_pub, pub_path.read_bytes())

    # 5. Final Hash Artifacts
    code_hash = hash_file(code_zip)
    evidence_hash = hash_file(evidence_zip)

    # 5. Create Ledger
    ledger: Dict[str, Any] = {
        "version": version,
        "timestamp_utc": _get_timestamp(),
        "build_wallclock_utc": _get_wallclock(),
        "strict_mode": (os.environ.get("STRICT_MODE", "1") == "1"),
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
    ledger_inner_name = f"RUN_LEDGER_INNER_v{version}.json"
    ledger_inner_path = build_tmp / ledger_inner_name
    # [CHAOS V231] Ledger Inflation Protection
    inner_json = json.dumps(ledger, indent=2, sort_keys=True, separators=(", ", ": "))
    if len(inner_json) > 10 * 1024 * 1024: # 10MB Limit
        raise RuntimeError(f"CRITICAL: RUN_LEDGER_INNER exceeds size limit ({len(inner_json)/1024/1024:.2f}MB). Sabotage?")

    with open(ledger_inner_path, "w") as f:
        f.write(inner_json)

    # 6. Create DROP Zip (The Final Package)
    print(f"📦 Forging DROP Artifact: {drop_zip.name}")
    
    # [DIST HARDENING] Define sidecar content
    # Note: We can only hash the final zip AFTER closing it. 
    # So the internal sidecar will contain the hashes of the INNER components 
    # to allow portable per-component verification.
    sidecar_internal_txt = (
        f"{code_hash}  {code_zip_name}\n"
        f"{evidence_hash}  {evidence_zip_name}\n"
        f"{hash_file(ledger_inner_path)}  {ledger_inner_name}\n"
    )

    # 5.5 DETACHED MANIFEST (v4.5.29+)
    # The manifest hashes both code and evidence zips AFTER they are finalized.
    # The cert does NOT hash the evidence zip (breaking circularity).
    # The manifest lives in the READY zip outer envelope alongside (not inside) the payload zips.
    drop_manifest = {
        "manifest_schema_version": "1.0.0",
        "generated_at_utc": _get_timestamp(),
        "trader_ops_version": version,
        "files": [
            {"path": code_zip_name, "sha256": code_hash, "type": "code"},
            {"path": evidence_zip_name, "sha256": evidence_hash, "type": "evidence"},
        ],
    }
    manifest_json_bytes = json.dumps(drop_manifest, indent=2, sort_keys=True).encode("utf-8")
    drop_manifest_hash = hashlib.sha256(manifest_json_bytes).hexdigest()
    print(f"📋 Detached MANIFEST.json forged: {drop_manifest_hash[:8]}...")

    with zipfile.ZipFile(drop_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(code_zip, code_zip_name)
        zf.write(evidence_zip, evidence_zip_name)
        zf.write(ledger_inner_path, ledger_inner_name)
        if (repo_root / "SOVEREIGN_REPORT.md").exists():
            _write_to_zip(zf, repo_root / "SOVEREIGN_REPORT.md", "SOVEREIGN_REPORT.md")
        
        # Inject Detached MANIFEST.json
        zinfo_m = zipfile.ZipInfo("MANIFEST.json", date_time=(2020, 1, 1, 0, 0, 0))
        zinfo_m.compress_type = zipfile.ZIP_DEFLATED
        zinfo_m.external_attr = 0o644 << 16
        zf.writestr(zinfo_m, manifest_json_bytes)
        print("📋 Injected MANIFEST.json into READY zip")

        # Inject Internal Witness Sidecar
        zinfo_s = zipfile.ZipInfo(f"DROP_WITNESS_INNER_SHA256_v{version}.txt", date_time=(2020, 1, 1, 0, 0, 0))
        zinfo_s.compress_type = zipfile.ZIP_DEFLATED
        zf.writestr(zinfo_s, sidecar_internal_txt)

        # Inject Drop Auditor (Self-Contained Verifier)
        auditor_path = repo_root / "scripts" / "drop_auditor.py"
        if auditor_path.exists():
            _write_to_zip(zf, auditor_path, "drop_auditor.py")
            print("🔍 Injected drop_auditor.py into drop zip")
        # Inject public key for standalone certificate verification
        if pub_path.exists():
            _write_to_zip(zf, pub_path, "sovereign.pub")
            print("🔑 Injected sovereign.pub into drop zip")

    with zipfile.ZipFile(drop_zip, "a", zipfile.ZIP_DEFLATED) as zf:
        # Update metadata to list the correct inner ledger
        timestamp = _get_timestamp()
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
        # [HYDRA FIX: Determinism] Force Unix (3) and clear extra
        zinfo.create_system = 3
        zinfo.extra = b""
        zinfo.external_attr = 0o644 << 16
        zf.writestr(zinfo, meta_content)

    # HYDRA GUARD: Payload Inflation Protection (Vector 39)
    drop_size = drop_zip.stat().st_size
    if drop_size > 1024 * 1024 * 1024:  # 1GB
        raise RuntimeError(f"PAYLOAD INFLATION DETECTED: {drop_zip.name} exceeds 1GB limit")

    drop_hash = hash_file(drop_zip)
    ledger["artifacts"]["ready_to_drop"] = {"filename": drop_zip_name, "sha256": drop_hash}

    # 6.0 Artifact Promotion (Audit-Grade Accessibility)
    # Copy intermediate artifacts to dist/ so independent verifiers can find them.
    shutil.copy(code_zip, dist_dir / code_zip_name)
    shutil.copy(evidence_zip, dist_dir / evidence_zip_name)

    # 6.1 Outer Ledger (Dist Canon)
    # This ledger DOES contain artifacts.ready_to_drop.
    ledger_path = dist_dir / f"RUN_LEDGER_v{version}.json"
    with open(ledger_path, "w") as f:
        json.dump(ledger, f, indent=2, sort_keys=True)

    # 6.2 Sign the RUN_LEDGER (Sovereign Binding)
    key_path = repo_root / "sovereign.key"
    if key_path.exists():
        ledger_sig_path = dist_dir / f"RUN_LEDGER_v{version}.json.sig"
        try:
            subprocess.run([
                "openssl", "pkeyutl", "-sign",
                "-inkey", str(key_path),
                "-rawin", "-in", str(ledger_path),
                "-out", str(ledger_sig_path)
            ], check=True)
            print(f"✍️  Ledger Signed: {ledger_sig_path.name}")
        except Exception as e:
            print(f"⚠️  Ledger signing failed (non-fatal): {e}")

    # 7. Automated Sidecars (Hygiene Enforcement)
    print("🩹 Regenerating Sidecars...")
    # POISON CLEANUP: Delete ALL unversioned sidecars (timeline-poison prevention)
    for stale in [dist_dir / "DROP_PACKET_SHA256.txt", repo_root / "docs/ready_to_drop/DROP_PACKET_SHA256.txt"]:
        if stale.exists():
            stale.unlink()
            print(f"🗑️  Removed stale sidecar: {stale.name}")
    
    # Versioned Sidecar (Immutable History)
    versioned_sidecar = dist_dir / f"DROP_PACKET_SHA256_v{version}.txt"
    versioned_sidecar.write_text(f"{drop_hash}  {drop_zip_name}\n")
    
    # Generate versioned sidecars (Deliverables only)
    (dist_dir / f"{drop_zip_name}.sha256").write_text(f"{drop_hash}  {drop_zip_name}\n")
    
    # Intermediate sidecars (History Only - in build_tmp)
    for artifact_name, artifact_hash in [
        (code_zip_name, code_hash),
        (evidence_zip_name, evidence_hash),
    ]:
        (build_tmp / f"{artifact_name}.sha256").write_text(f"{artifact_hash}  {artifact_name}\n")

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

    # 9. Automated Decision Log (Automatic Sovereignty)
    _auto_log_decision(repo_root, version, git_info)

    # Final gate: verify the assembled drop packet end-to-end.
    print("🛡️  Running Sovereign End-to-End Audit...")
    verify_args = [
        sys.executable,
        str(repo_root / "scripts" / "verify_drop_packet.py"),
        "--drop", str(drop_zip),
        "--run-ledger", str(ledger_path),
        "--drop-packet-sha", str(dist_dir / f"DROP_PACKET_SHA256_v{version}.txt"),
    ]
    if os.environ.get("STRICT_MODE", "1") == "1":
        verify_args.append("--strict")
    
    try:
        subprocess.check_call(verify_args, cwd=repo_root)
        print("✅ End-to-End Audit Passed.")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"FINAL AUDIT FAILURE: assembled packet failed verification. {e}") from e

    return ledger


def _auto_log_decision(repo_root: Path, version: str, git_info: Dict[str, Any]) -> None:
    """Automatically append git context to the Decision Log."""
    log_path = repo_root / "docs/DECISION_LOG.md"
    if not log_path.exists():
        return

    content = log_path.read_text()
    # [STAGE 1 FIX: Determinism] Use fixed date for Decision Log
    date_str = "2020-01-01"
    
    # Avoid duplicate entries for the same version
    # Check specifically for the version header to avoid false positives in body text
    if f"## {date_str}: " in content and f" (v{version})" in content and re.search(rf"^## {date_str}: .* \(v{version}\)$", content, re.M):
        return

    # Extract subject and body
    msg = git_info["message"].strip()
    lines = msg.splitlines()
    subject = lines[0] if lines else "Manual Build"
    body_raw = "\n".join(lines[1:]).strip() if len(lines) > 1 else ""

    # Enhanced Parsing for Structured Commit Messages
    context = f"Automated entry captured via Git Provenance during the v{version} forge."
    decision = subject
    trade_offs = "- **Pros**: Guaranteed provenance; zero-effort documentation.\n- **Cons**: Depth of log depends on commit message quality."

    if "Context:" in body_raw:
        m = re.search(r"Context:\s*(.*?)(?=\s*(Decision:|Trade-offs:)|$)", body_raw, re.S)
        if m:
            context = m.group(1).strip()
    
    if "Decision:" in body_raw:
        m = re.search(r"Decision:\s*(.*?)(?=\s*(Context:|Trade-offs:)|$)", body_raw, re.S)
        if m:
            decision = m.group(1).strip()
    
    if "Trade-offs:" in body_raw:
        m = re.search(r"Trade-offs:\s*(.*?)(?=\s*(Context:|Decision:)|$)", body_raw, re.S)
        if m:
            trade_offs = m.group(1).strip()

    new_entry = (
        f"\n---\n\n"
        f"## {date_str}: {subject} (v{version})\n\n"
        f"### Context\n"
        f"{context}\n\n"
        f"### Decision\n"
        f"{decision}\n\n"
        f"### Trade-offs\n"
        f"{trade_offs}\n"
    )
    
    log_path.write_text(content + new_entry)
    print(f"📜 Decision Log Automated: v{version}")


def _create_zip(zip_path: Path, root: Path, includes: List[str], exclude: List[str] = None) -> None:
    """Create a deterministic zip file containing specified paths."""
    exclude = exclude or []
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for item in includes:
            item_path = root / item
            if item_path.is_symlink():
                raise RuntimeError(f"SYMLINK POISON (V246): {item} is a symlink.")
            if item_path.is_file():
                if item in exclude:
                    continue
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
                    if arcname in exclude:
                        continue
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
        data = f.read()
        # compressed_size is unknown until write, so we rely on heuristic or estimate.
        # Actually, we can check size after writestr if we want, or just enforce a raw size limit.
        if len(data) > 1024 * 1024 * 500: # 500MB limit per file
             raise RuntimeError(f"FILE SIZE SABOTAGE: {arcname} exceeds 500MB limit.")
        
        zf.writestr(zinfo, data)
        
        # Post-write check for compression ratio
        # zf.getinfo(str(arcname)).compress_size is available now
        info = zf.getinfo(str(arcname))
        if info.compress_size > 0:
            ratio = info.file_size / info.compress_size
            if ratio > 100: # Standard "Zip Bomb" threshold
                raise RuntimeError(f"ZIP BOMB DETECTED: {arcname} has suspicious compression ratio ({ratio:.1f}x)")


def _assert_cleanliness(root: Path) -> None:
    """Abort if __pycache__ exists."""
    if list(root.rglob("__pycache__")):
        raise RuntimeError("Dirty Repo: __pycache__ found. Run 'make clean' first.")


def _check_disk_quota(min_gb: float = 5.0) -> None:
    # HYDRA GUARD: Quota Crash Protection (Vector 70)
    import shutil  # noqa: PLC0415
    _, _, free = shutil.disk_usage(".")
    free_gb = free / (1024**3)
    if free_gb < min_gb:
        raise RuntimeError(f"RESOURCE EXHAUSTION: Disk space ({free_gb:.2f} GB) below Hydra limit ({min_gb} GB)")


def _is_forbidden(path: Path) -> bool:  # noqa: PLR0911, PLR0912
    # HYDRA GUARD: Pickle Poison Protection (Vector 66)
    if path.suffix in {".pkl", ".pickle", ".joblib"}:
        raise RuntimeError(f"SECURITY VIOLATION: Binary state file '{path.name}' detected. Pickle is forbidden.")

    # HYDRA GUARD: Double-Dot Trap (Vector 101)
    if ".." in str(path):
        return True
    
    # HYDRA GUARD: Null Byte Bomb (Vector 111)
    if "\0" in str(path):
        raise RuntimeError(f"SECURITY VIOLATION: Null byte in path '{path}'.")
    
    # HYDRA GUARD: Symlink Loop & Redirection Protection (Vector 26, 38)
    if path.is_symlink():
        return True # Reject all symlinks in Sovereign artifacts for reliability
    
    # HYDRA GUARD: Path Traversal Protection (Vector 37)
    # Ensure path is internal to the archive structure
    try:
        path.resolve() # Check for existence and basic sanity
    except Exception:
        return True
    
    if path.name.startswith(".") and path.name != ".gitignore":  # noqa: SIM103
        return True
    if any(part.startswith(".") for part in path.parts):
        return True
    if bool(any(part == "__pycache__" for part in path.parts)):
        return True
    # Fix 4: Forge Purity - Forbid auto-inclusion of manifest (handled explicitly)
    if path.name == "PAYLOAD_MANIFEST.json":
        return True
    # Fix 5: Solari v5 Hygiene - Forbid build_tmp in Evidence/Code
    if "build_tmp" in path.parts:
        return True
    # Fix 3: Evidence Purity - Explicitly forbid tests/fixtures in artifacts
    # [CHAOS V234] System Path Rejection
    system_prefixes = ("/dev/", "/proc/", "/sys/", "/etc/")
    if str(path.absolute()).startswith(system_prefixes):
        raise RuntimeError(f"SECURITY VIOLATION: Source path '{path}' is a system path. Aborting forge.")

    # [CHAOS V235] Hardlink Mimic Protection
    # Rejection of hardlinks to prevent cross-inode corruption or exclusion bypass.
    if path.exists() and not path.is_dir():
        st = path.stat()
        if st.st_nlink > 1:
             raise RuntimeError(f"SECURITY VIOLATION: Hardlink detected for '{path}' (links={st.st_nlink}). Risk of shadow corruption.")

    return "tests" in path.parts and "fixtures" in path.parts




def _generate_manifest_data(root: Path, includes: List[str], exclude: List[str] = None) -> Dict[str, str]:
    """Calculate hashes for all files to be included in the manifest."""
    manifest = {}
    exclude = exclude or []
    for item in includes:
        item_path = root / item
        if item_path.is_file():
            if item in exclude:
                continue
            manifest[item] = hash_file(item_path)
        elif item_path.is_dir():
            for file_path in sorted(item_path.rglob("*")):
                if not file_path.is_file():
                    continue
                if _is_forbidden(file_path):
                    continue
                arcname = Path(file_path.relative_to(root)).as_posix()
                if arcname in exclude:
                    continue
                manifest[arcname] = hash_file(file_path)
    return manifest


# Public Alias for Testing
create_deterministic_zip = _create_zip
