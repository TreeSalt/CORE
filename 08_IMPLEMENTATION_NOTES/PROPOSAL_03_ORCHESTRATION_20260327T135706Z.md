---
DOMAIN: 03_ORCHESTRATION
MODEL: qwen3.5:9b
TIER: cruiser
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

```python
import re
from pathlib import Path


def extract_last_error(error_ledger_path: str, domain_id: str) -> str:
    path = Path(error_ledger_path)
    content = path.read_text()
    
    pattern = rf'##\s*{re.escape(domain_id)}.*?(?=\n##|\Z)'
    match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
    
    if match:
        return match.group(0).strip()
    
    return ""


def enrich_packet(escalation_path: str, error_text: str) -> None:
    path = Path(escalation_path)
    content = path.read_text()
    
    if "## Root Cause" in content:
        return
    
    with open(path, 'a', encoding='utf-8') as f:
        f.write(f"\n\n## Root Cause\n{error_text}\n")


def enrich_all_pending(escalations_dir: str, error_ledger_path: str) -> int:
    count = 0
    escalations_dir = Path(escalations_dir)
    
    for file_path in escalations_dir.glob('ESCALATION_*.md'):
        content = file_path.read_text()
        
        if "## Root Cause" not in content:
            domain_id = file_path.stem.replace('ESCALATION_', '').strip()
            error_text = extract_last_error(error_ledger_path, domain_id)
            
            if error_text:
                enrich_packet(str(file_path), error_text)
                count += 1
    
    return count
```