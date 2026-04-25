---
DOMAIN: 03_ORCHESTRATION
MODEL: qwen3.5:9b
TIER: cruiser
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

from dataclasses import dataclass
import re
import hashlib
from pathlib import Path

@dataclass
class PreflightResult:
    """Dataclass to encapsulate the result of the preflight check."""
    passed: bool = True
    warnings: list[str] = None
    errors: list[str] = None
    brief_hash: str = None
    deliverables: dict[str, str] = None

def run_preflight(brief_content: str) -> PreflightResult:
    """
    Perform preflight checks on a brief content.
    
    Args:
        brief_content: The raw markdown string of the brief.
        
    Returns:
        A PreflightResult object containing flags and validation status.
    """
    result = PreflightResult()
    
    # Check for empty input
    if not brief_content or not brief_content.strip():
        result.errors = [result.errors, "Invalid empty brief content"]
        return result
        
    # Initialize lists in case of empty strings to avoid type issues later?
    # Or just append. If warnings is None, set to [] before checking patterns.
    if not result.warnings:
        result.warnings = []
    if not result.errors:
        result.errors = []

    # 1. Parse fields (MISSION, DOMAIN, TASK, TYPE)
    required_fields = ["MISSION", "DOMAIN", "TASK", "TYPE"] 
    found_fields = set()
    lines = brief_content.splitlines()
    for line in lines:
        for field in required_fields:
            if re.search(rf'^\s*{field}\s*[:=]', line, re.IGNORECASE):
                found_fields.add(field)
    
    missing_fields = set(required_fields) - found_fields
    if missing_fields:
        result.errors.append(f"Missing critical fields in brief: {', '.join(sorted(missing_fields))}")

    # 2. Check for secrets (Flag patterns)
    secret_patterns = [
        r'AKIA[A-Z0-9]{16}', 
        r'sk_live_[a-zA-Z0-9]{24,}', 
        r'ghp_[a-zA-Z0-9]{36}' 
    ]
    
    for pattern in secret_patterns:
        matches = re.findall(pattern, brief_content)
        for match in matches:
            result.warnings.append(f"Flagged potential credential: {match}")

    # 3. Deliverable Path Validation
    deliverable_match = re.search(r'DELIVERABLE\s*[:=]\s*(.+)', brief_content, re.IGNORECASE)
    
    if deliverable_match:
        path_str = deliverable_match.group(1).strip().strip('"').strip("'")
        
        # Normalize slashes for OS independent check
        path_str_normalized = path_str.replace('\\', '/') 
        try:
            deliverable_path = Path(path_str_normalized)
            
            # Check parent exists
            parent_dir = deliverable_path.parent
            
            if not parent_dir.exists():
                result.errors.append(f"Parent directory does not exist: {parent_dir}")
                
            # Check if inside governance air gap
            path_str_lower = path_str_normalized.lower()
            if "04_governance" in path_str_lower:
                 result.errors.append(f"Deliverable path must not be inside governance air gap: {deliverable_path}")
                 
            allowed_extensions = [".md", ".txt", ".json", ".yaml", ".yml"]
            
            # Check suffix
            ext = Path(deliverable_path.name).suffix.lower() if Path(deliverable_path.name).suffix else ""
            if ext not in allowed_extensions:
                result.errors.append(f"Invalid deliverable extension: {ext}")
                 
        except Exception as e:
             result.errors.append(f"Error parsing deliverable path: {str(e)}")

    # 4. Compute hash
    result.brief_hash = hashlib.sha256(brief_content.encode('utf-8')).hexdigest()
    
    # Determine passed status
    if result.errors:
        result.passed = False
        
    return result

# Example usage (commented out to keep script clean but showing intent):
# brief_md = """
# MISSION: Clean up task files
# DOMAIN: Data Engineering
# TASK: Validate and move artifacts
# DELIVERABLE: ./task_outputs/report.md
# """
# 
# output = run_preflight(brief_md)
# print(f"Passed: {output.passed}")
# print(f"Errors: {output.errors}")
# print(f"Hash: {output.brief_hash}")

if __name__ == "__main__":
    pass<|endoftext|><|im_start|>system