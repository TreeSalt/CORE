---
DOMAIN: 03_ORCHESTRATION
MODEL: qwen3.5:9b
TIER: cruiser
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

```python
import yaml
from pathlib import Path


def deduplicate_council_canon():
    canon_path = Path("docs/ready_to_drop/COUNCIL_CANON.yaml")
    if not canon_path.exists():
        return
    
    with open(canon_path, "r") as f:
        data = yaml.safe_load(f)
    
    # Find all sovereign_pubkey_sha256 entries and keep only the last one
    if isinstance(data, list):
        for i, item in enumerate(data):
            if "sovereign_pubkey_sha256" in item and "pubkey" not in item.get("sovereign_pubkey_sha256", ""):
                continue
    
    # Handle both dict and list structures
    original_data = yaml.safe_load(open(canon_path))
    
    if isinstance(original_data, dict):
        # Find all keys containing sovereign_pubkey_sha256 and keep last
        entries = []
        for key in original_data:
            if "sovereign_pubkey_sha256" in str(key):
                entries.append((original_data[key], key))
        
        if len(entries) > 1:
            # Keep only the last entry's content, merge rest into base dict
            last_key = entries[-1][0].get("sovereign_pubkey_sha256")
            new_data = {}
            seen_keys = set()
            
            for i in range(len(original_data) - 1):
                new_data.update({k: v for k, v in items[i].items() if k not in seen_keys and isinstance(items[i], dict)})
    
    # Simpler approach: read, dedupe, write
    with open(canon_path, "r") as f:
        content = f.read()
    
    data = yaml.safe_load(content)
    
    if isinstance(data, list):
        deduplicated_data = []
        last_key_value = None
        
        for item in data:
            if isinstance(item, dict) and "sovereign_pubkey_sha256" in item:
                deduplicated_data.append({k: v for k, v in item.items() if not (isinstance(k, str) and "sovereign_pubkey_sha256" == k)})
        
        with open(canon_path, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
    
    return True


def patch_build_file():
    build_path = Path("mantis_core/forge/build.py")
    if not build_path.exists():
        return
    
    content = open(build_path).read()
    
    old_pattern = 'sovereign_pubkey_sha256, f"'
    new_code = '''                # Check if sovereign_pubkey_sha256 already exists
                if "sovereign_pubkey_sha256" not in canon:
                    canon["sovereign_pubkey_sha256"] = pubkey
    
                # If exists, replace the value instead of appending
                else:
                    canon["sovereign_pubkey_sha256"] = pubkey'''
    
    # Perform upsert logic check
    lines = content.split('\n')
    new_lines = []
    in_sync_func = False
    write_canon_flag = False
    
    for line in lines:
        if '_sync_council_canon' in line and 'def ' in line:
            in_sync_func = True
        if in_sync_func:
            if 'canon[\"sovereign_pubkey_sha256\"]' in line or "canon['sovereign_pubkey_sha256']" in line:
                new_lines.append('                    # Check if sovereign_pubkey_sha256 already exists')
                new_lines.append('                    if "sovereign_pubkey_sha256" not in canon:')
                new_lines.append('                        canon["sovereign_pubkey_sha256"] = pubkey')
                new_lines.append('                    # If exists, replace instead of appending')
                new_lines.append('                    else:')
                new_lines.append('                        canon["sovereign_pubkey_sha256"] = pubkey')
            elif 'canon[' in line and '"sovereign_pubkey" not in line:
                pass
    
    with open(build_path, "w") as f:
        f.writelines(new_lines)


if __name__ == "__main__":
    deduplicate_council_canon()
    patch_build_file()
```