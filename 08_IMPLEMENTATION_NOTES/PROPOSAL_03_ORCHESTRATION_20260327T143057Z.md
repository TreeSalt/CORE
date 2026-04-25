---
DOMAIN: 03_ORCHESTRATION
MODEL: qwen3.5:9b
TIER: cruiser
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

```python
import pathlib
from typing import Optional

def _find_error_in_ledger(ledger_content: str, domain_id: str) -> str:
    """
    Extracts the last error entry from the ledger content for a given domain_id.
    
    Args:
        ledger_content (str): Raw text content of ERROR_LEDGER.md
        domain_id (str): Identifier for the specific domain/error
        
    Returns:
        str: Error text after `domain_id` up to next header, empty string if not found.
    """
    idx = ledger_content.rfind(domain_id)
    if idx == -1: 
        return ""
    
    # Find start of this line (previous newline before domain_id)
    start_line_idx = ledger_content.rfind('\n', 0, idx)
    if start_line_idx == -1: 
        start_line_idx = 0
        
    remaining = ledger_content[idx:]
    
    # Look for next main header to define the end of this error block
    next_header_pos = remaining.find('\n\n#')
    
    text_end = idx + next_header_pos if next_header_pos != -1 else len(ledger_content)
    
    return ledger_content[start_line_idx+1:text_end].strip()

def enrich_packet(error_ledger_path: str, domain_id: str, escalation_path: str) -> bool:
    """
    Enriches a single escalation file with the last error from the ledger.
    Returns True if updated, False otherwise (already enriched or missing).
    
    Args:
        error_ledger_path (str): Path to ERROR_LEDGER.md
        domain_id (str): Domain identifier
        escalation_path (str): Path to the .md file to enrich
        
    Returns:
        bool: True if content was appended, False otherwise.
    """
    ledger_file = pathlib.Path(error_ledger_path)
    
    # Ledger must exist and be readable
    if not ledger_file.exists(): 
        return False
    
    try:
        ledger_content = ledger_file.read_text(encoding='utf-8')
    except Exception: 
        return False
        
    error_text = _find_error_in_ledger(ledger_content, domain_id)
    
    # Error must exist in ledger
    if not error_text: 
        return False

    escalation_file = pathlib.Path(escalation_path)
    existing_content = ""
    
    # Read file content to check for duplication and build new string
    try:
        if escalation_file.exists():
            existing_content = escalation_file.read_text(encoding='utf-8')
        # Skip update if domain_id or error_text already found
        if domain_id in existing_content or error_text in existing_content:
            return False
    except Exception:
        return False
    
    # Append error block to file
    new_content = existing_content + f"\n\n## Root Cause\n\n{error_text}"
    
    try:
        escalation_file.write_text(new_content, encoding='utf-8')
        return True
    except Exception: 
        return False

def enrich_all_pending(escalations_dir_path: str, domain_id: str, error_ledger_path: Optional[str] = None) -> int:
    """
    Enriches all pending escalation files in a directory with the last error from ledger.
    
    Args:
        escalations_dir_path (str): Root directory containing ESCALATION_*.md files.
        domain_id (str): Domain identifier to lookup in ledger.
        error_ledger_path (Optional[str]): Custom path to ERROR_LEDGER.md. 
            Defaults to 'escalations_dir/docs/ERROR_LEDGER.md'.
            
    Returns:
        int: Number of files successfully updated.
    """
    if error_ledger_path is None:
        dir_path = pathlib.Path(escalations_dir_path).resolve()
        # Default construction as per thought block logic.
        error_ledger_path = str(dir_path / 'docs' / 'ERROR_LEDGER.md')

    dir_path = pathlib.Path(escalations_dir_path).resolve()
    updated_count = 0
    
    ledger_file = pathlib.Path(error_ledger_path)
    if not ledger_file.exists(): 
        return 0
    
    try:
        ledger_content = ledger_file.read_text(encoding='utf-8')
    except Exception: 
        return 0
        
    error_text = _find_error_in_ledger(ledger_content, domain_id)
    
    if not error_text: 
        return 0

    # Loop through all escalation files in the directory
    for file_path in dir_path.glob("ESCALATION_*.md"):
        escalation_file = pathlib.Path(file_path)
        
        # Read existing content
        try:
            current_content = escalation_file.read_text(encoding='utf-8')
        except Exception: 
            continue
        
        # Skip if already enriched
        if domain_id in current_content or error_text in current_content: 
            continue
            
        # Append and save
        new_content = current_content + f"\n\n## Root Cause\n\n{error_text}"
        
        try:
            escalation_file.write_text(new_content, encoding='utf-8')
            updated_count += 1
        except Exception: 
            continue
            
    return updated_count
```<|endoftext|><|im_start|>user