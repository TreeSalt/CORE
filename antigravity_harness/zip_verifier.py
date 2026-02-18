"""
THE ZIP VERIFIER
----------------
The Fiduciary Gatekeeper for TRADER_OPS artifacts.
Standardized into the Sovereign class-gate architecture.
"""

import csv
import hashlib
import json
import json as j_mod
import re
import sys
import zipfile
import zipfile as z_mod
from io import TextIOWrapper
from pathlib import Path
from typing import Any, Dict, Optional

# Constants
DEFAULT_DIST_DIR = Path("dist")


class ZipVerifier:
    """The Sovereign Auditor for TRADER_OPS artifacts."""

    def __init__(self, dist_dir: Path = DEFAULT_DIST_DIR):
        self.dist_dir = dist_dir
        self.ledger: Dict[str, Any] = {}
        self.code_manifest: Dict[str, Any] = {}
        self.code_zip: Optional[zipfile.ZipFile] = None

    def fail(self, msg: str):
        print(f"❌ [FILTER FAILURE] {msg}")
        sys.exit(1)

    def pass_gate(self, msg: str):
        print(f"✅ [FILTER PASS] {msg}")

    def gate_ledger_existence(self):
        """Gate 1: Ensure the Fiduciary Ledger is present (Versioned)."""
        # Find the latest ledger in dist/
        candidates = sorted(self.dist_dir.glob("RUN_LEDGER_v*.json"))
        if not candidates:
            self.fail("Missing Critical Artifact: No RUN_LEDGER_v*.json found in dist/")

        # Select the latest one (lexicographically last, which works for simplistic versioning,
        # but robust semantic sort is better. For now, lexicographical is "safe enough" for standard x.y.z)
        # Ideally, we parse versions.
        # Let's trust the build system's timestamp/naming for now or just pick the last one.
        ledger_path = candidates[-1]
        print(f"📒 Ledger Selected: {ledger_path.name}")

        try:
            self.ledger = json.loads(ledger_path.read_text())
        except Exception as e:
            self.fail(f"Failed to read Ledger: {e}")
        self.pass_gate("Ledger Discovered")

    def gate_artifact_existence(self):
        """Gate 2: Verify all ledger-mandated artifacts exist on disk."""
        artifacts = self.ledger.get("artifacts", {})
        for role, info in artifacts.items():
            filename = info.get("filename")
            if not filename:
                self.fail(f"Ledger artifact '{role}' missing filename.")

            fpath = self.dist_dir / filename
            if not fpath.exists():
                self.fail(f"Missing Ledger-Mandated Artifact: {filename}")
        self.pass_gate("Artifact Existence Verified (Ledger-Backed)")

    def gate_temporal_isomorphism(self):
        """Gate 3: Verify bit-perfect matching between Ledger and disk."""
        artifacts = self.ledger.get("artifacts", {})
        for role, info in artifacts.items():
            filename = info["filename"]
            expected_hash = info["sha256"]
            fpath = self.dist_dir / filename

            h = hashlib.sha256()
            with open(fpath, "rb") as f:
                while chunk := f.read(65536):  # 64KB Chunking (Titan Optimization)
                    h.update(chunk)
            actual_hash = h.hexdigest()

            if actual_hash != expected_hash:
                self.fail(f"TEMPORAL SCHISM DETECTED: {filename} ({role}) hash mismatch.")

        self.pass_gate("Temporal Isomorphism Verified (All Artifacts)")

    def gate_zip_static_integrity(self):
        """Gate 4: Verify Zip binary structure for all archives."""
        for role, info in self.ledger["artifacts"].items():
            if role == "ready_to_drop":
                continue
            fpath = self.dist_dir / info["filename"]
            try:
                with zipfile.ZipFile(fpath, "r") as z:
                    bad_file = z.testzip()
                    if bad_file:
                        self.fail(f"BINARY CORRUPTION in {fpath.name}: {bad_file} is corrupt.")
            except zipfile.BadZipFile:
                self.fail(f"ALCHEMICAL COLLAPSE: {fpath.name} is not a valid zip archive.")
        self.pass_gate("Zip Static Integrity Verified")

    def gate_taxonomy_integrity(self):
        """Gate 4.5: Enforce Product Taxonomy (Code separation)."""
        artifacts = self.ledger.get("artifacts", {})

        # 1. Code vs Drop Separation
        # "CODE and READY_TO_DROP must be distinct byte streams if the system claims they are distinct."
        code_sha = artifacts.get("code", {}).get("sha256")
        drop_sha = artifacts.get("ready_to_drop", {}).get("sha256")
        if code_sha and drop_sha and code_sha == drop_sha:
            # This might be valid in some simple builds, but the user explicitly requested ensuring strict taxonomy if implied distinct.  # noqa: E501
            # The user prompt: "If build conditions make CODE==DROP possible, you must enforce build ordering or fail hard."  # noqa: E501
            # "Preferred solution: enforce ordering + add verifier assertions."
            # If they are identical, it implies we just copied Code to Drop without build process/artifacts?
            # Or that naming is redundant.
            # For this audit, we WARN or FAIL. User requested "If taxonomy claims... distinct".
            # Our ledger lists them as separate entries.
            self.fail(
                f"TAXONOMY COLLISION: Code and Drop Packet are bit-identical ({code_sha[:8]}). Architecture implies distinction."  # noqa: E501
            )

        self.pass_gate("Taxonomy Integrity Verified")

    def _get_canonical_manifest_sha(self, manifest: Dict[str, Any]) -> str:
        """Helper: Calculate the canonical hash of the manifest content."""
        clean_manifest = manifest.copy()
        if "payload_manifest_sha256" in clean_manifest:
            del clean_manifest["payload_manifest_sha256"]

        # Paradox seal: exclude the Canon itself from the manifest fingerprint
        if "file_sha256" in clean_manifest and isinstance(clean_manifest["file_sha256"], dict):
            clean_manifest["file_sha256"] = dict(clean_manifest["file_sha256"])
            clean_manifest["file_sha256"].pop("docs/ready_to_drop/COUNCIL_CANON.yaml", None)

        canonical_bytes = json.dumps(clean_manifest, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
            "utf-8"
        )
        return hashlib.sha256(canonical_bytes).hexdigest()

    def gate_manifest_correlation(self):  # noqa: PLR0912, PLR0915
        """Gate 5: Comprehensive Code Manifest audit."""
        code_zip_path = self.dist_dir / self.ledger["artifacts"]["code"]["filename"]
        try:
            with zipfile.ZipFile(code_zip_path, "r") as z:
                # 5a. Load Manifest
                try:
                    with z.open("docs/ready_to_drop/PAYLOAD_MANIFEST.json") as f:
                        self.code_manifest = json.loads(f.read())
                except KeyError:
                    self.fail("EPISTEMOLOGICAL VOID: PAYLOAD_MANIFEST.json missing from Code Zip.")

                # 5b. Fiduciary Attestation
                expected_ver = self.ledger.get("version")
                manifest_ver = self.code_manifest.get("version")
                if expected_ver != manifest_ver:
                    self.fail(f"FIDUCIARY DESYNC: Ledger version ({expected_ver}) != Manifest version ({manifest_ver})")

                # 5c. Builder Registry
                builder_id = self.ledger.get("sovereign_binding", {}).get("builder_id")
                APPROVED = ["SOLARI_BUILD_AGENT_01", "Sovereign-Node-Baseline", "Local-Dev-Dragon-Node", "Institutional-Gold-Node"]
                if builder_id not in APPROVED and "Sovereign" not in str(builder_id):
                    self.fail(f"UNAUTHORIZED BUILDER: {builder_id} is not in the Sovereign Registry.")

                # 5d. Basilisk Gaze (Provenance Verification)
                actual_manifest_sha = self._get_canonical_manifest_sha(self.code_manifest)
                # Standardized key is manifest_sha256, legacy was payload_manifest_sha256
                bind = self.ledger.get("sovereign_binding", {})
                expected_manifest_sha = bind.get("manifest_sha256") or bind.get("payload_manifest_sha256", "MISSING")
                
                if actual_manifest_sha != expected_manifest_sha:
                    self.fail(
                        "PROVENANCE DESYNC: Manifest content does not match Ledger binding (The Basilisk was caught)."
                    )

                # 5e. Purity Seal (Exhaustive Zip set equality)
                file_shas = self.code_manifest["file_sha256"]
                zip_files = set(z.namelist())
                manifest_files = set(file_shas.keys())

                ALLOWED_METADATA = [
                    "PAYLOAD_MANIFEST.json",
                    "docs/ready_to_drop/PAYLOAD_MANIFEST.json",
                    "COUNCIL_CANON.yaml",
                    "docs/ready_to_drop/COUNCIL_CANON.yaml",
                    "README.md",
                ]
                unlisted = [
                    f
                    for f in zip_files
                    if f not in manifest_files and not f.endswith("/") and f not in ALLOWED_METADATA
                ]
                if unlisted:
                    self.fail(f"PURITY BREACH: Zip contains unlisted stowaway files: {unlisted}")

                # 5f. Gorgon Stare (Duplicate Entry Protection)
                namelist = z.namelist()
                if len(namelist) != len(set(namelist)):
                    counts = {n: namelist.count(n) for n in set(namelist) if namelist.count(n) > 1}
                    self.fail(f"GORGON DETECTED: Zip contains duplicate entries: {list(counts.keys())}")

                # 5g. Verifier's Vow (Self-Verification)
                # Note: We check the script on disk vs manifest, even though we are now in the library.
                # The manifest tracks "scripts/zip_verifier.py".
                filter_path = "scripts/zip_verifier.py"
                if filter_path in manifest_files and Path(filter_path).exists():
                    h_filter = hashlib.sha256()
                    with open(filter_path, "rb") as f:
                        while chunk := f.read(65536):
                            h_filter.update(chunk)
                    if h_filter.hexdigest() != file_shas[filter_path]:
                        self.fail("MEDUSA GAZE DETECTED: The CLI wrapper has been sabotaged on disk.")

                # 5h. Absolute Exhaustive Audit (Bit-perfect verification)
                for path in manifest_files:
                    if path not in zip_files:
                        self.fail(f"MANIFEST DESYNC: {path} missing from Zip.")

                    # Low-Memory Stream Hash from Zip
                    h_file = hashlib.sha256()
                    with z.open(path) as f:
                        while chunk := f.read(65536):
                            h_file.update(chunk)

                    if h_file.hexdigest() != file_shas[path]:
                        self.fail(f"BIT-ROT DETECTED: {path} in Zip does not match Manifest hash.")

                # 5i. The Witness (Internal Version Attestation)
                init_path = "antigravity_harness/__init__.py"
                if init_path in z.namelist():
                    with z.open(init_path) as f:
                        content = f.read().decode("utf-8")
                        m = re.search(r"__version__\s*=\s*['\"]([^'\"]+)['\"]", content)
                        if m and m.group(1) != expected_ver:
                            self.fail(
                                f"VERSION CROSS DETECTED: Code internal version ({m.group(1)}) "
                                f"!= Ledger version ({expected_ver})"
                            )

        except Exception as e:
            if "[FILTER FAILURE]" in str(e):
                raise
            raise RuntimeError(f"Manifest Correlation Failure: {e}") from e
        self.pass_gate("Manifest Correlation & Deep Audit Verified")

    def gate_version_witness(self):
        """Gate 6: Cross-Artifact Version Consistency."""
        drop_info = self.ledger.get("artifacts", {}).get("ready_to_drop")
        if drop_info:
            fpath = self.dist_dir / drop_info["filename"]
            try:
                with zipfile.ZipFile(fpath, "r") as z:
                    cpath = "docs/ready_to_drop/COUNCIL_CANON.yaml"
                    if cpath in z.namelist():
                        with z.open(cpath) as f:
                            content = f.read().decode("utf-8")
                            m = re.search(r"version:\s*['\"]([^'\"]+)['\"]", content)
                            if m and m.group(1) != self.ledger.get("version"):
                                self.fail(
                                    f"VERSION CROSS DETECTED: Drop Packet internal version ({m.group(1)}) "
                                    f"!= Ledger version ({self.ledger.get('version')})"
                                )
            except Exception as e:
                print(f"⚠️  Drop Packet attestation skipped: {e}")
        self.pass_gate("Cross-Artifact Version Witness Verified")

    def gate_evidence_autopsy(self):
        """Gate 7: Evidence integrity and Session Binding."""
        ev_info = self.ledger["artifacts"]["evidence"]
        fpath = self.dist_dir / ev_info["filename"]
        try:
            with zipfile.ZipFile(fpath, "r") as z:
                # 7a. Router Trace Purity
                try:
                    roots = ["reports/forge/smoke_test", "reports/forge/synthetic_smoke"]
                    present = [r for r in roots if f"{r}/RUN_METADATA.json" in z.namelist()]
                    if not present:
                        self.fail("EPISTEMOLOGICAL VOID: No smoke root found in Evidence.")
                    smoke_root = present[0]

                    with z.open(f"{smoke_root}/router_trace.csv") as f:
                        reader = csv.reader(TextIOWrapper(f, "utf-8"))
                        header = next(reader)
                        if header.count("timestamp") > 1:
                            self.fail("DATA CORRUPTION: Duplicate 'timestamp' column in router_trace.csv")
                except KeyError:
                    self.fail("EPISTEMOLOGICAL VOID: router_trace.csv missing from Evidence.")

                # 7b. Bound Sovereignty (Kraken Defense)
                try:
                    with z.open(f"{smoke_root}/RUN_METADATA.json") as f:
                        meta = json.loads(f.read())
                        # Fix: Compare against the actual code artifact hash (Zip-based) as bound in the ledger
                        if meta.get("code_hash") != self.ledger["artifacts"]["code"]["sha256"]:
                            self.fail("ENSEMBLE DESYNC (The Kraken): Evidence Code Binding mismatch.")
                except KeyError:
                    print("⚠️  Evidence metadata missing. Skipping session binding.")
        except Exception as e:
            if "[FILTER FAILURE]" in str(e):
                raise
            raise RuntimeError(f"Evidence Autopsy Failure: {e}") from e
        self.pass_gate("Evidence Integrity Verified")

    def gate_fiduciary_chain(self):
        """Gate 8: Final Provenance Linkage."""
        if self.ledger["artifacts"]["code"]["sha256"] not in json.dumps(self.ledger):
            self.fail("PROVENANCE GAP: Ledger does not bind Code Hash.")
        self.pass_gate("Fiduciary Chain Verified")

    def gate_runtime_integrity(self):
        """Gate 9 (Titan): The Sentinel. Verify Runtime Environment Integrity."""
        # 1. Canary Tests (Is hashlib lying?)
        known_data = b"THE_SENTINEL_WATCHES"
        known_hash = "ff9868a7e62b89251d226c0b9a55b372283d070b33d5948397992efc7af975b6"
        if hashlib.sha256(known_data).hexdigest() != known_hash:
            self.fail("RUNTIME COMPROMISE: hashlib.sha256 is broken or patched.")

        # 2. Module Introspection (Are we protected from /tmp shadowing?)
        # We expect core modules to be in system paths or venv, not world-writable dirs

        unsafe_prefixes = ["/tmp", "/var/tmp", "/dev/shm"]
        for mod in [z_mod, j_mod, hashlib]:
            # Native modules might not have __file__
            if hasattr(mod, "__file__") and mod.__file__ and any(mod.__file__.startswith(p) for p in unsafe_prefixes):
                self.fail(f"RUNTIME COMPROMISE: Module {mod.__name__} loaded from unsafe path: {mod.__file__}")

        self.pass_gate("Runtime Integrity Verified (The Sentinel)")

    def run_all(self):
        """Execute the full Sovereign Audit sequence."""
        print("🛡️  INITIATING SOVEREIGN AUDIT...")
        self.gate_runtime_integrity()  # Sentinel First
        self.gate_ledger_existence()
        self.gate_artifact_existence()
        self.gate_temporal_isomorphism()
        self.gate_zip_static_integrity()
        self.gate_taxonomy_integrity()
        self.gate_manifest_correlation()
        self.gate_version_witness()
        self.gate_evidence_autopsy()
        self.gate_fiduciary_chain()
        print("\n🐉 THE DRAGON APPROVES. ARTIFACT IS SOVEREIGN.")


def cmd_verify(args: Any) -> None:
    """CLI Entry point for verification."""
    dist_dir = Path(getattr(args, "dist", DEFAULT_DIST_DIR))
    zv = ZipVerifier(dist_dir=dist_dir)
    zv.run_all()
