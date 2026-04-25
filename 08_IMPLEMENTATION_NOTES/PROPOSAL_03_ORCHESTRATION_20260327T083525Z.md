---
DOMAIN: 03_ORCHESTRATION
MODEL: qwen3.5:9b
TIER: cruiser
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

```python
import pathlib
import re


def extract_last_error(error_ledger_path: str, domain_id: str) -> str:
    ledger_path = pathlib.Path(error_ledger_path)
    if not ledger_path.exists():
        return ""
    
    content = ledger_path.read_text()
    # Find most recent error entry for the given domain
    pattern = rf"## {re.escape(domain_id)}\s*\n(?=Reason:|Error:)"
    matches = re.findall(pattern, content, re.DOTALL)
    
    if not matches:
        return ""
    
    # Return the last (most recent) error entry for the domain
    entries = []
    temp_matches = re.findall(rf"## {re.escape(domain_id)}\s*\n((?:.|\n)*?)(?=^## {re.escape(domain_id)}|)", content, re.MULTILINE | re.DOTALL)
    if temp_matches:
        for match in reversed(temp_matches):
            entries.append(match.strip())
            if len(entries) >= 1:
                break
        return entries[0] if entries else ""
    
    return ""


def enrich_packet(escalation_path: str, error_text: str) -> None:
    escalation_path = pathlib.Path(escalation_path)
    content = escalation_path.read_text()
    
    # Add Root Cause section at the end of the file
    root_cause = "\n\n## Root Cause"
    if not error_text.strip():
        root_cause += "\n(No error details available)"
    else:
        root_cause += f"\n{error_text}"
    
    new_content = content + root_cause
    
    escalation_path.write_text(new_content)


def enrich_all_pending(escalations_dir: str, error_ledger_path: str) -> int:
    escalations_dir = pathlib.Path(escalations_dir)
    ledger_path = pathlib.Path(error_ledger_path)
    
    enriched_count = 0
    
    for file in sorted(escalations_dir.glob("ESCALATION_*.md")):
        content = file.read_text()
        
        if "## Root Cause" not in content:
            # Extract domain_id from filename (e.g., ESCALATION_PROD.md -> "PROD")
            base_name = file.stem
            if "." in base_name:
                domain_id = base_name.rsplit(".", 1)[0]
            else:
                domain_id = base_name
            
            error_text = extract_last_error(str(ledger_path), domain_id)
            enrich_packet(str(file), error_text)
            enriched_count += 1
    
    return enriched_count
```