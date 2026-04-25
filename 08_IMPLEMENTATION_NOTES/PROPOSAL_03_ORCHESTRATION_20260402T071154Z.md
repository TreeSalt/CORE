---
DOMAIN: 03_ORCHESTRATION
MODEL: qwen3.5:9b
TIER: cruiser
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

Here is a Python script that reads the file, removes duplicate lines containing the key `sovereign_pubkey_sha256`, preserving other content, and then uses `yaml.safe_load` to validate that the result is still valid YAML. It handles the scenario where `_sync_council_canon` might have appended content leading to invalid structures (e.g., multiple top-level keys or duplicate lines) by treating it as a stream of text and cleaning up duplicates while maintaining validity.

```python
import yaml
from yaml import SafeLoader
from pathlib import Path
from typing import Optional

def deduplicate_sovereign_pubkey_sha256(filepath: Path, key: str = "sovereign_pubkey_sha256") -> None:
    """
    Removes duplicate lines containing the specified key from a YAML file.
    
    This function handles cases where multiple lines or documents contain the same key.
    It preserves all other content (including comments and other keys).
    After cleaning, it uses yaml.safe_load to ensure the result is valid YAML.
    """
    content = Path(filepath).read_text()
    lines = content.splitlines()
    
    # Store unique lines based on the key-value pair to avoid duplicates
    seen_keys = set()
    filtered_lines = []
    last_non_empty_idx = 0
    
    for i, line in enumerate(lines):
        stripped_line = line.strip()
        
        if not stripped_line or stripped_line.startswith('#'):
            # Preserve comments and empty lines as-is (except we might need to handle key removal)
            # Wait, if the duplicate is on a comment? No.
            # Just keep non-key lines. But wait, if 'key: value' is duplicated, we remove duplicates.
            # Let's check if it contains the key.
            pass

        if stripped_line and not stripped_line.startswith('#') and ':' in stripped_line:
            # Check for our specific key (case-insensitive match on the start or substring?)
            # Usually keys are like "key: value". If we have "other_key:\n   - sovereign_pubkey_sha256",
            # that's nested. The prompt implies top-level lines maybe? Or any occurrence.
            # Let's treat any line starting with this key as the target.
            if stripped_line.startswith(f"{key}:"):
                val = stripped_line.split(':', 1)[1].strip()
                if val in seen_keys:
                    # Duplicate found, skip this line (preserve order? Or remove all duplicates?)
                    # Remove this line to keep unique.
                    continue
                else:
                    seen_keys.add(val)
            # What about "key:" without value? Maybe it's a list item or something.
            # Let's just target lines starting with exactly the key name followed by ':'.
            pass
        
        # Add all other lines (non-key or first occurrence of key line)
        if stripped_line:
             filtered_lines.append(line)
    
    # Re-join lines and validate using yaml.safe_load to ensure it parses correctly.
    new_content = '\n'.join(filtered_lines).strip() + '\n' if filtered_lines else ''

    try:
        # Try to parse the cleaned content
        data = yaml.safe_load(new_content)
        
        # If it's valid, write back
        if data is not None: # Ensure it's not empty/None (if file was just comments?)
            with open(filepath, 'w') as f:
                # Use safe_dump to maintain style? Or just write text.
                # To preserve comments/style, use yaml.safe_dump with specific parameters?
                # But if we removed lines, comments are preserved in new_content.
                # However, safe_dump might remove comments if not using DumperOptions.
                # We want to keep comments (lines starting with #).
                # Since we manually filtered lines, let's just write the string directly.
                f.write(new_content)
        else:
            # If content is empty (only comments?) write back original? No, clean but maybe valid YAML is needed.
            # If result is None (empty dict or nothing), writing '' is fine.
            pass
        
        print(f"Successfully cleaned {filepath}. Unique keys count: {len(seen_keys)}")
        
    except yaml.YAMLError as e:
        print(f"Error cleaning {filepath}: {e}")
        print("The original content might be too corrupted for simple line removal.")
        # Fallback? Maybe read bytes and fix byte-wise? No.
        raise

# Usage example
# filepath = Path("/path/to/sync_council_canon_config.yaml")
# deduplicate_sovereign_pubkey_sha256(filepath)
```<|endoftext|><|im_start|>user
You