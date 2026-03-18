---
DOMAIN: 03_ORCHESTRATION
MODEL: qwen2.5-coder:32b
TIER: heavy
TYPE: IMPLEMENTATION
STATUS: RATIFIED
---

Below is a proposal for the `rotate_trust_root.py` script that adheres to the specified constraints and requirements:

```python
#!/usr/bin/env python3

import hashlib
import pathlib
import sys
import re
import os
import json

def compute_hash(file_path):
    """Compute SHA256 hash of the file's raw bytes."""
    with open(file_path, "rb") as f:
        raw_bytes = f.read()
    return hashlib.sha256(raw_bytes).hexdigest()

def find_files_with_old_hash(old_hash, root_dir):
    """Find all files containing the old hash."""
    matching_files = []
    for path in pathlib.Path(root_dir).rglob('*'):
        if path.is_file() and path.suffix in ('.py', '.yaml', '.json'):
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
                if old_hash in content:
                    matching_files.append(path)
    return matching_files

def replace_hash_in_file(file_path, old_hash, new_hash):
    """Replace the old hash with the new hash in the file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    new_content = content.replace(old_hash, new_hash)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

def verify_no_old_hash(old_hash, root_dir):
    """Verify no instances of the old hash remain."""
    for path in pathlib.Path(root_dir).rglob('*'):
        if path.is_file() and path.suffix in ('.py', '.yaml', '.json'):
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
                if old_hash in content:
                    return False
    return True

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 rotate_trust_root.py <public_key_file> [--old-hash OLDHASH]")
        sys.exit(1)

    public_key_file = sys.argv[1]
    old_hash = None

    # Parse optional --old-hash argument
    if '--old-hash' in sys.argv:
        old_hash_index = sys.argv.index('--old-hash')
        if len(sys.argv) > old_hash_index + 1:
            old_hash = sys.argv[old_hash_index + 1]
        else:
            print("Error: --old-hash provided without a hash value.")
            sys.exit(1)

    # Compute the new hash
    new_hash = compute_hash(public_key_file)
    if len(new_hash) != 64:
        print(f"Error: Computed hash {new_hash} does not match expected format (64 hex characters).")
        sys.exit(1)

    print(f"Computed new hash: {new_hash}")

    # If old hash is not provided, compute it from a temporary file (for testing purposes)
    if not old_hash:
        temp_file_path = 'temp_key.pub'
        try:
            with open(temp_file_path, 'wb') as f:
                f.write(open(public_key_file, 'rb').read().strip())  # Simulate old incorrect hash
            old_hash = compute_hash(temp_file_path)
        finally:
            os.remove(temp_file_path)
        print(f"Computed old hash (for testing): {old_hash}")

    # Find all files with the old hash
    root_dir = pathlib.Path(__file__).parent.parent  # Assuming script is in scripts/
    matching_files = find_files_with_old_hash(old_hash, root_dir)
    if not matching_files:
        print("No files containing the old hash were found.")
        sys.exit(0)

    # Replace the old hash with the new hash
    modified_files = []
    for file_path in matching_files:
        replace_hash_in_file(file_path, old_hash, new_hash)
        modified_files.append(file_path)
        print(f"Modified file: {file_path}")

    # Verify no instances of the old hash remain
    if verify_no_old_hash(old_hash, root_dir):
        print("Verification successful: No instances of the old hash remain.")
    else:
        print("Verification failed: Instances of the old hash remain.")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

### Explanation:

1. **Hash Computation**: The `compute_hash` function reads the public key file in raw bytes and computes its SHA256 hash using `hashlib`.

2. **File Search**: The `find_files_with_old_hash` function searches through all `.py`, `.yaml`, and `.json` files recursively from the root directory to find files containing the old hash.

3. **Hash Replacement**: The `replace_hash_in_file` function replaces occurrences of the old hash with the new hash in the identified files.

4. **Verification**: The `verify_no_old_hash` function checks that no instances of the old hash remain in the codebase.

5. **Main Function**: The `main` function orchestrates the process:
   - Parses command-line arguments.
   - Computes the new hash and optionally the old hash.
   - Finds and modifies files containing the old hash.
   - Verifies that the old hash has been successfully replaced.

### Testing:

- **Hash Computation**: The script computes the new hash and verifies it matches the expected format (64 hex characters).
- **Temporary File**: If the old hash is not provided, the script creates a temporary file to simulate an old incorrect hash and computes its hash.
- **File Replacement**: The script replaces the old hash with the new hash in all relevant files and prints a summary of modified files.
- **Verification**: The script verifies that no instances of the old hash remain in the codebase.

### Usage:

```bash
python3 scripts/rotate_trust_root.py keys/sovereign.pub [--old-hash OLDHASH]
```

This script is designed to be fail-safe and adhere strictly to the provided constraints.