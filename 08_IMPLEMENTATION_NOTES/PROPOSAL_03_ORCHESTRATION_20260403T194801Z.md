---
DOMAIN: 03_ORCHESTRATION
MODEL: qwen3.5:9b
TIER: cruiser
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

```python
from pathlib import Path

def dedup_canon():
    canon_path = Path("docs/ready_to_drop/COUNCIL_CANON.yaml")
    content = canon_path.read_text()
    lines = content.splitlines()
    seen = set()
    unique_lines = []
    removed_count = 0
    for line in lines:
        if line not in seen:
            seen.add(line)
            unique_lines.append(line)
        else:
            removed_count += 1

    reconstructed_content = "\n".join(unique_lines)
    if content.endswith("\n"):
        reconstructed_content += "\n"
    
    canon_path.write_text(reconstructed_content)
    print(removed_count)
```<|endoftext|><|im_start|>user