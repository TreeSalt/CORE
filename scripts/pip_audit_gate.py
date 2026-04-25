import subprocess
import sys
import json
import os
from typing import List, Optional, Tuple, Set, Dict, Any, Union
from dataclasses import dataclass, field

# --- Configuration & Constants ---
SEVERITY_SCORES = {
    "CRITICAL": 4, 
    "HIGH": 3, 
    "MEDIUM": 2, 
    "LOW": 1 
}

# --- Data Models ---
@dataclass(frozen=True)
class Vulnerability:
    """Parsed vulnerability record."""
    name: str
    package: str
    fix_version: Optional[str] = None
    severity: str = "UNKNOWN"

@dataclass(frozen=True)
class AuditResult:
    """Aggregated audit results."""
    total_packages_scanned: int
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    # List of Vulnerability objects
    vulnerabilities: List[Vulnerability] = field(default_factory=list)

# --- Core Logic Functions ---

def run_pip_audit(requirements_file: str, output_format: str = "json") -> Tuple[List[Dict], int]:
    """
    Runs pip-audit against the specified requirements file and returns raw JSON data.
    
    Args:
        requirements_file: Path to requirements file (e.g., 'requirements.txt').
        output_format: Desired output format for pip-audit ('json' or 'text').
        
    Returns:
        Tuple of (List[Dict] parsed vulnerability dicts, int total_packages_scanned).
    """
    try:
        # Basic command construction
        cmd = ["pip-audit", f"--format={output_format}", requirements_file]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        
        # Parse stdout as JSON if requested, else handle text
        if output_format == "json":
            try:
                data = json.loads(result.stdout.decode('utf-8'))
            except json.JSONDecodeError as e:
                raise RuntimeError(f"JSON parsing error from pip-audit: {e}")
            
            # Extract vulnerabilities and package counts
            vulns_raw = data.get("vulnerabilities", [])
            total_packages = len(data.get("packages", []))
            
            return (vulns_raw, total_packages)
        else:
            # If text output, we rely on standard exit code logic.
            # For this script's simplicity, we assume 'json' is the target for automation.
            raise RuntimeError(f"Text format not fully handled in this implementation, use --format=json")

    except subprocess.CalledProcessError as e:
        # pip-audit might fail with specific exit codes for different reasons
        stderr_msg = e.stderr.decode('utf-8') if hasattr(e, 'stderr') else ""
        print(f"Command failed: {e}", file=sys.stderr)
        if e.returncode == 0: 
             # Some versions of pip-audit return 0 even with vulnerabilities.
             pass
        elif "not found" in stderr_msg.lower() or f"command not found" in stderr_msg.lower():
            raise FileNotFoundError("pip-audit command not found. Ensure it is installed.")
        else:
             print(f"Pip-audit error: {stderr_msg}", file=sys.stderr)
        
    except subprocess.TimeoutExpired:
         raise TimeoutError("Pip-audit timed out.")

def load_allowlist(allowlist_path: Optional[str]) -> Set[str]:
    """Load allowed packages from a JSON file."""
    if not allowlist_path or not os.path.exists(allowlist_path):
        return set()
    
    try:
        with open(allowlist_path, 'r') as f:
            content = json.load(f)
            # Support simple list of strings or specific key like {"packages": [...]}
            raw_allowlist = content.get("packages", [])
            if not isinstance(raw_allowlist, list):
                raise ValueError("Allowlist file must contain a list of package names.")
            return set(raw_allowlist)
    except json.JSONDecodeError:
        raise RuntimeError(f"Invalid JSON format in allowlist file: {allowlist_path}")

def parse_vulnerabilities(raw_vulns: List[Dict], fail_on_severity: str) -> AuditResult:
    """Parse raw vulnerability JSON into AuditResult dataclass."""
    vuln_list = []
    
    for item in raw_vulns:
        # Standardize severity field based on pip-audit structure
        sev = "UNKNOWN"
        if isinstance(item.get("severity"), str):
            sev = item["severity"]
        elif isinstance(item.get("severity"), dict):
            sev = item["severity"].get("name", "UNKNOWN")
        
        # Create Vulnerability object
        vuln_obj = Vulnerability(
            name=item.get("name", "unknown"),
            package=item.get("package", "unknown"),
            fix_version=item.get("fix_version"),
            severity=sev
        )
        vuln_list.append(vuln_obj)

    # Aggregate counts
    result = AuditResult(total_packages_scanned=0, vulnerabilities=vuln_list)
    
    for v in vuln_list:
        if v.name in result.vulnerabilities or result.critical_count == 0 and len(result.vulnerabilities)==0: # Avoid dup counting in list
             continue
        
        # Simple aggregation based on parsed dict keys (reusing counts from raw_json might be better, but here we aggregate)
        # Wait, we need to count from the input raw_vulns which is already a list.
        
        if v.severity in SEVERITY_SCORES:
            score = SEVERITY_SCORES[v.severity]
            if score > result.high_count and v.severity == "HIGH":
                 # Logic error here: need to map properly to counts
                 pass 
    # Actually simpler: just count occurrences in list
    for v in vuln_list:
        sev = v.severity
        if sev == "CRITICAL": result.critical_count += 1
        elif sev == "HIGH": result.high_count += 1
        elif sev == "MEDIUM": result.medium_count += 1
        elif sev == "LOW": result.low_count += 1

    return result

def evaluate_audit_results(audit_result: AuditResult, allowlisted_ids: Set[str], fail_on_severity: str) -> bool:
    """
    Evaluate aggregated results against thresholds. Returns True if audit passed.
    
    Args:
        audit_result: Aggregate result object from parse_vulnerabilities.
        allowlisted_ids: Set of package names allowed despite vulnerabilities.
        fail_on_severity: Minimum severity to trigger failure (default HIGH).
        
    Returns:
        bool: True if audit passes, False otherwise.
    """
    # Check Severity Gate
    threshold_score = SEVERITY_SCORES.get(fail_on_severity.upper(), 3) # Default to HIGH=3
    
    for vuln in audit_result.vulnerabilities:
        # Skip allowlisted packages
        if vuln.name in allowlisted_ids:
            continue
        
        score = SEVERITY_SCORES.get(vuln.severity, 0)
        if score >= threshold_score:
            return False
            
    return True

def main():
    """Main execution entry point."""
    parser = None # Using simple arguments for this script to keep it self-contained
    
    # Default behavior: Audit requirements.txt (or pip list), fail on CRITICAL/HIGH/LOW/MEDIUM if specified
    # In a real script, we might parse CLI args here. 
    # For this example, we define defaults and allow override via simple sys.argv logic below or manual inputs.
    
    # Simulating arguments parsing for generic usage:
    requirements_file = "requirements.txt"
    fail_on_severity = "HIGH"
    allowlist_path = None
    
    if len(sys.argv) > 1:
        # Parse CLI args if provided (Simple implementation)
        for arg in sys.argv[1:]:
            if arg.startswith("-"): 
                continue # Skip help/other flags for this demo
            elif arg == "--requirements":
                 i = sys.argv.index(arg)
                 requirements_file = sys.argv[i+1]
            elif arg == "--severity":
                 i = sys.argv.index(arg)
                 fail_on_severity = sys.argv[i+1]
            elif arg == "--allowlist":
                 allowlist_path = sys.argv[i+1]

    print(f"Starting Audit for: {requirements_file}")
    print(f"Failing on severity: {fail_on_severity.upper()}")
    
    if not os.path.exists(requirements_file):
        # Try to scan system installed packages if no file found (optional)
        # For this demo, we'll assume requirements.txt exists or default.
        print("Requirements file not found, using default fallback logic.")
        pass

    try:
        # 1. Run Audit
        raw_data, total_packages = run_pip_audit(requirements_file)
        
        if not raw_data: 
             # pip-audit might return empty list if no vulns.
             pass
        
        print(f"Scanned {total_packages} packages.")
        
        # 2. Allowlist Loading
        allowlisted_ids = load_allowlist(allowlist_path)
        
        # 3. Parse Results
        audit_result = parse_vulnerabilities(raw_data, fail_on_severity)
        
        # Note: The `parse_vulnerabilities` function needs to map counts correctly 
        # which was slightly refactored above mentally to count from list items.
        # To make it correct in code block:
        # Re-assigning for clarity in final output
        c = sum(1 for v in audit_result.vulnerabilities if v.severity == "CRITICAL")
        h = sum(1 for v in audit_result.vulnerabilities if v.severity == "HIGH")
        m = sum(1 for v in audit_result.vulnerabilities if v.severity == "MEDIUM")
        l = sum(1 for v in audit_result.vulnerabilities if v.severity == "LOW")
        
        # Fix the AuditResult object with correct counts
        audit_result.critical_count = c
        audit_result.high_count = h
        audit_result.medium_count = m
        audit_result.low_count = l

        # 4. Evaluation
        passed = evaluate_audit_results(audit_result, allowlisted_ids, fail_on_severity)
        
        if passed:
            print("\n[ SUCCESS ] Audit Passed.")
            return 0
        else:
            print("\n[ FAILURE ] Audit Failed.")
            return 1
            
    except Exception as e:
        print(f"\nError during audit process: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
