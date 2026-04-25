---
DOMAIN: 03_ORCHESTRATION
MODEL: qwen3.5:9b
TIER: cruiser
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

import re
import sys
import json
import yaml
from pathlib import Path

def main():
    # Check for arguments
    if len(sys.argv) < 2:
        report = {"status": "failed", "failures": ["Missing brief path argument"]}
        print(json.dumps(report))
        sys.exit(1)

    brief_path = Path(sys.argv[1])
    
    # Load Brief Content
    try:
        content = brief_path.read_text()
    except FileNotFoundError:
        report = {"status": "failed", "failures": [f"File not found: {brief_path}"]}
        print(json.dumps(report))
        sys.exit(1)

    # Load Domains Config (Relative to execution context or project root usually)
    domains_path = Path("04_GOVERNANCE/DOMAINS.yaml")
    
    # Determine valid domain list from the config file
    # If path is not found, we treat it as a failure state for validation purposes
    valid_domains = set()
    try:
        with open(domains_path) as f:
            raw_data = yaml.safe_load(f)
            # YAML config usually provides a list of domain strings or a dict mapping IDs to objects. 
            # Assuming the list format based on typical usage in these contexts.
            if isinstance(raw_data, list):
                valid_domains = set(raw_data)
            elif isinstance(raw_data, dict):
                # If it's a dict, keys might be the domains
                valid_domains = set(raw_data.keys())
    except FileNotFoundError:
        report = {"status": "failed", "failures": ["Could not load domains configuration (missing 04_GOVERNANCE/DOMAINS.yaml)"]}
        print(json.dumps(report))
        sys.exit(1)
    except Exception as e:
        report = {"status": "failed", "failures": [f"Error loading domains configuration: {e}"]}
        print(json.dumps(report))
        sys.exit(1)

    failures = []

    # --- Validation Checks ---

    # Check 1: DELIVERABLE or File:
    if re.search(r'(?i)\b(DELIVERABLE|File:)', content):
        pass
    else:
        failures.append("Missing DELIVERABLE or File: line")

    # Check 2 & 3: DOMAIN and TYPE values
    # Case sensitive extraction for standard key names
    domain_match = re.search(r'\bDOMAIN\s*:\s*(\S+)', content)
    type_match = re.search(r'\bTYPE\s*:\s*(\S+)', content)

    domain_value = domain_match.group(1) if domain_match else None
    type_value = type_match.group(1) if type_match else None

    # Requirement 2: Valid Domain ID
    if domain_value is not None and domain_value not in valid_domains:
        failures.append(f"Invalid domain value: {domain_value}")

    # Requirement 3: Valid Type
    if type_value and type_value not in {"IMPLEMENTATION", "ARCHITECTURE", "STRATEGIC_ARCHITECTURE", "TEST"}:
        failures.append(f"Invalid type value: {type_value}")

    # Requirement 2 & Logic for Missing Keys:
    # If the line is missing entirely, it counts as a failure per strict interpretation of "matches a valid domain ID".
    if domain_value is None:
         failures.append("Missing DOMAIN line")
    
    # --- Requirement 4 & 5: Import Requirements ---

    # Check if EXACT IMPORTS section exists (Requirement 4)
    has_exact_imports = "EXACT IMPORTS" in content

    # Determine need for imports based on specific Domains (Requirement 5)
    needs_imports = False
    
    # If TYPE is TEST
    if type_value == "TEST":
        needs_imports = True
        
    # If Domain is specific IDs
    elif domain_value and domain_value in {"00_PHYSICS_ENGINE", "02_RISK_MANAGEMENT"}:
        needs_imports = True

    # Check for failure condition (If needed but missing)
    if needs_imports and not has_exact_imports:
        failures.append("Missing EXACT IMPORTS section for required context")

    # --- Reporting ---
    report_obj = {"status": "passed"}
    if failures:
        report_obj["status"] = "failed"
        report_obj["failures"] = failures
    
    print(json.dumps(report_obj))
    
    sys.exit(0)

if __name__ == "__main__":
    main()<|endoftext|><|im_start|>user