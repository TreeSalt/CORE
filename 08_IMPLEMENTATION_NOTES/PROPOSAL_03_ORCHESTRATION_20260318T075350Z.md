---
DOMAIN: 03_ORCHESTRATION
MODEL: qwen2.5-coder:32b
TIER: heavy
TYPE: IMPLEMENTATION
STATUS: RATIFIED
---

Certainly! Below is a Python script that meets the specified requirements for automating the trust root key rotation across the entire codebase.

```python
#!/usr/bin/env python3

import hashlib
import pathlib
import json
import sys
import re
import os

def compute_hash(file_path):
    """Compute the SHA256 hash of the raw bytes of the given file."""
    with open(file_path, "rb") as f:
        raw_bytes = f.read()
    return hashlib.sha256(raw_bytes).hexdigest()

def find_and_replace(old_hash, new_hash, root_dir):
    """Recursively find and replace the old hash with the new hash in all relevant files."""
    modified_files = []
    for path in pathlib.Path(root_dir).rglob('*.{py,yaml,json}'):
        if path.is_file():
            with open(path, 'r') as f:
                content = f.read()
            if old_hash in content:
                modified_files.append(str(path))
                content = content.replace(old_hash, new_hash)
                with open(path, 'w') as f:
                    f.write(content)
    return modified_files

def verify_no_old_hash(old_hash, root_dir):
    """Verify that no instances of the old hash remain in the codebase."""
    for path in pathlib.Path(root_dir).rglob('*.{py,yaml,json}'):
        if path.is_file():
            with open(path, 'r') as f:
                content = f.read()
            if old_hash in content:
                return False
    return True

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/rotate_trust_root.py keys/sovereign.pub [--old-hash OLDHASH]")
        sys.exit(1)

    public_key_path = sys.argv[1]
    old_hash = None

    if len(sys.argv) > 2 and sys.argv[2] == '--old-hash' and len(sys.argv) > 3:
        old_hash = sys.argv[3]
    else:
        print("ERROR: --old-hash OLDHASH must be provided.")
        sys.exit(1)

    if not os.path.isfile(public_key_path):
        print(f"ERROR: The file {public_key_path} does not exist.")
        sys.exit(1)

    new_hash = compute_hash(public_key_path)
    if not re.match(r'^[0-9a-f]{64}$', new_hash):
        print(f"ERROR: Computed hash {new_hash} is not in the expected format.")
        sys.exit(1)

    print(f"New hash computed: {new_hash}")

    root_dir = os.getcwd()
    modified_files = find_and_replace(old_hash, new_hash, root_dir)

    print(f"Files modified: {modified_files}")

    if verify_no_old_hash(old_hash, root_dir):
        print("Verification successful: No instances of the old hash remain.")
    else:
        print("Verification failed: Instances of the old hash remain.")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

### Explanation:

1. **compute_hash**: Computes the SHA256 hash of the raw bytes of the given public key file.
2. **find_and_replace**: Recursively searches for and replaces the old hash with the new hash in all `.py`, `.yaml`, and `.json` files within the specified directory.
3. **verify_no_old_hash**: Ensures that no instances of the old hash remain in the codebase.
4. **main**: Parses command-line arguments, computes the new hash, and performs the key rotation.

### Usage:

```sh
python3 scripts/rotate_trust_root.py keys/sovereign.pub --old-hash OLDHASH
```

This script will:
1. Compute the new hash of the public key.
2. Find and replace the old hash with the new hash in all relevant files.
3. Print a summary of files modified.
4. Verify that no instances of the old hash remain.

### Constraints:

- The script uses only allowed imports.
- No external dependencies are used.
- The script fails closed on any constraint breach.
- The hash is computed from raw bytes, ensuring no changes due to trailing newlines.