---
DOMAIN: 03_ORCHESTRATION
MODEL: qwen3.5:9b
TIER: sprinter
TYPE: IMPLEMENTATION
STATUS: RATIFIED
---

```python
#!/usr/bin/env python3
"""
Trust Root Key Rotation Script (Sprint Tier)
Domain: 03_ORCHESTRATION
Security Class: INTERNAL
Mission: Automate sovereign key rotation and hash propagation.

CRITICAL SECURITY NOTE:
Hashes MUST be computed from RAW BYTES of the public key file.
strip() or .encode() on text mode violates verifier compatibility.
"""
import hashlib
import pathlib
import sys
import re
import os


def compute_public_key_hash(public_key_path):
    """Computes SHA-256 hash of a public key file's raw bytes."""
    if not os.path.isfile(public_key_path):
        sys.exit(f"ERROR: Public key file not found: {public_key_path}")
    try:
        with open(public_key_path, "rb") as f:
            raw_bytes = f.read()
        if len(raw_bytes) == 0:
            sys.exit(f"ERROR: Public key file is empty: {public_key_path}")
        raw_hash = hashlib.sha256(raw_bytes).hexdigest()
        return raw_hash
    except Exception as e:
        sys.exit(f"ERROR: Failed to read public key ({e})")


def find_config_files(root):
    """Finds all Python, YAML, JSON config files recursively."""
    try:
        extensions = ('*.py', '*.yaml', '*.yml', '*.json')
        paths = []
        for ext in extensions:
            paths.extend(root.rglob(ext))
        return [p for p in paths if os.path.isfile(p)]
    except Exception as e:
        sys.exit(f"ERROR: Failed to scan directory ({e})")


def replace_hash_in_files(root_path, old_hash, new_hash):
    """Replaces the old SHA-256 hash with the new one in all config files."""
    modified = []

    # Validate Hash Formats
    if len(old_hash) != 64 or not re.match(r'^[0-9a-f]+$', old_hash):
        sys.exit(f"ERROR: Invalid OLD HASH format. Must be 64 hex chars: {old_hash}")
    if len(new_hash) != 64 or not re.match(r'^[0-9a-f]+$', new_hash):
        sys.exit(f"ERROR: Invalid NEW HASH format. Must be 64 hex chars: {new_hash}")

    for path in find_config_files(root_path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            if old_hash not in content:
                continue
            new_content = content.replace(old_hash, new_hash)
            if new_content != content:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                print(f"MODIFIED: {path}")
                modified.append(str(path))
        except PermissionError:
            sys.exit(f"ERROR: Permission denied on file: {path}")
        except Exception as e:
            # Handle other errors gracefully (e.g., encoding issues in files)
            print(f"WARNING: Failed to modify file ({e})")

    return modified


def verify_old_hash_gone(root_path, old_hash):
    """Checks if the old hash is removed from all config files."""
    try:
        found = False
        for path in find_config_files(root_path):
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            if old_hash in content:
                print(f"FAILURE: Old hash still exists in: {path}")
                found = True
        return not found
    except Exception as e:
        sys.exit(f"ERROR: Verify check failed ({e})")


def main():
    # Parse command line arguments
    if len(sys.argv) < 3:
        print("Usage: python trust_root_rotation.py <old_hash> <new_hash>")
        print("Hashes must be SHA-256 hex digests of the RAW public key.")
        sys.exit(1)

    old_hash_arg = sys.argv[1]
    new_hash = sys.argv[2]

    DOMAIN = "03_ORCHESTRATION"
    SECURITY_CLASS = "INTERNAL"

    print(f"TRUST ROOT ROTATION STARTED")
    print(f"Old Hash: {old_hash_arg}")
    print(f"New Hash: {new_hash}")

    # Replace hash in all config files (Standard lib only)
    root_dir = pathlib.Path('.')
    replace_hash_in_files(root_dir, old_hash_arg, new_hash)

    if verify_old_hash_gone(root_dir, old_hash_arg):
        print("SUCCESS: All instances of old hash removed.")
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
```