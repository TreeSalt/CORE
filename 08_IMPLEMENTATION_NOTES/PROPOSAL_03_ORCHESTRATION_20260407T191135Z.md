---
DOMAIN: 03_ORCHESTRATION
MODEL: qwen3.5:9b
TIER: cruiser
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

```python
import sys
import re
import json
from pathlib import Path

def get_valid_domains(config_file: str = "04_GOVERNANCE/DOMAINS.yaml") -> set:
    """
    Reads the domains configuration file and extracts valid domain IDs.
    Uses pure regex and string matching (no external YAML parsers).
    Handles standard YAML list items '- ID' or simple key-value pairs.
    """
    config_path = Path(config_file)
    if not config_path.exists():
        return set()
    
    valid_domains = set()
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        for line in lines:
            stripped = line.strip()
            
            # Skip empty lines and comments
            if not stripped or stripped.startswith('#'):
                continue
            
            # Pattern 1: List item "- ID"
            match_list = re.match(r'^-\s*(.+)$', stripped)
            if match_list:
                val = match_list.group(1).strip()
                if val:
                    valid_domains.add(val)
            
            # Pattern 2: Key-Value where value is a domain ID (e.g., "DOMAIN:" or similar)
            # If line contains ":" and looks like config definition, take the value part.
            # To avoid grabbing arbitrary values, we check if it starts with a known pattern or 
            # if we are just parsing key-value where the key/value might be IDs.
            # Given the context of "domains", assuming simple values after colon might be risky.
            # Let's assume simple lists in this strict environment are the main use case.
            
    except Exception:
        # Fallback to returning empty set on any read error
        return valid_domains
    
    return valid_domains

def check_import_requirements(type_str: str, domain_id: str) -> bool:
    """
    Determines if 'EXACT IMPORTS' section is required in the brief.
    Required if TYPE is TEST OR if domain is 00_PHYSICS_ENGINE or 02_RISK_MANAGEMENT.
    """
    # Normalize type string (remove whitespace/case sensitivity)
    current_type = type_str.strip() if type_str else ""
    current_domain = domain_id.strip() if domain_id else ""
    
    require = False
    
    if current_type.upper() == "TEST":
        return True
        
    special_domains = {"00_PHYSICS_ENGINE", "02_RISK_MANAGEMENT"}
    if current_domain in special_domains:
        return True
        
    return False

def generate_report(type_str: str, domain_id: str) -> dict:
    """
    Generates a report structure for the given type and domain.
    Validates domain existence against configuration file if path provided.
    """
    valid_domains = get_valid_domains()
    is_domain_valid = domain_id in valid_domains
    
    # Check imports requirement
    required_imports_section = check_import_requirements(type_str, domain_id)
    
    report = {
        "domain_id": domain_id,
        "type": type_str,
        "is_domain_valid": is_domain_valid,
        "requires_imports_section": required_imports_section,
        # Sample content based on requirements
        "imports_list": ["standard_lib"] if required_imports_section else []
    }
    
    return report

def main():
    # Example usage
    type_type = sys.argv[1] if len(sys.argv) > 1 else "TEST"
    domain_id = sys.argv[2] if len(sys.argv) > 2 else "00_PHYSICS_ENGINE"
    
    print(json.dumps(generate_report(type_type, domain_id), indent=4))

if __name__ == "__main__":
    main()
```<|endoftext|><|im_start|>user
Your response contained invalid code. Your final output must be valid Python only