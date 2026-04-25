---
DOMAIN: 08_CYBERSECURITY
MODEL: qwen3.5:9b
TIER: cruiser
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

#!/usr/bin/env python3
"""
Pip Audit Gate - Security Scanning Tool.
Analyzes requirements files against a mock vulnerability database and applies filtering rules.
"""

import argparse
import json
import os
import sys
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class SeverityLevel(Enum):
    """Defines the severity levels for security vulnerabilities."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Vulnerability:
    """Data class representing a specific vulnerability found in a package."""
    name: str
    version: str
    severity: SeverityLevel
    description: str
    fix_version: Optional[str] = None
    cve_ids: List[str] = field(default_factory=list)


@dataclass
class AuditResult:
    """Data class representing the aggregated result for a package scan."""
    package_name: str
    status: str
    is_critical: bool
    vulnerabilities_count: int
    details: List[Dict[str, Any]] = field(default_factory=list)


def load_allowlist(allowlist_path: Optional[str] = None) -> Dict[str, Any]:
    """Load an optional allowlist configuration file to skip specific packages."""
    if not allowlist_path or not os.path.exists(allowlist_path):
        return {"packages": {}, "version_rules": []}

    config = {"packages": {}, "version_rules": []}
    
    try:
        with open(allowlist_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                parts = line.split(',')
                if len(parts) == 3:
                    pkg_name, _, allowed_str = parts
                    # Parse boolean-ish string for allowlist logic
                    is_allowed = str(allowed_str).lower() in ("true", "yes", "1")
                    config["packages"][pkg_name] = {
                        "allowed": is_allowed,
                        "reason": f"Explicitly allowed by {allowlist_path}"
                    }
    except FileNotFoundError:
        print(f"Allowlist file '{allowlist_path}' not found. Skipping.", file=sys.stderr)
    except Exception as e:
        print(f"Error reading allowlist file: {e}", file=sys.stderr)
        
    return config


def parse_vulnerabilities(vulns: List[Vulnerability], fail_on_severity: SeverityLevel = SeverityLevel.HIGH) -> List[AuditResult]:
    """Convert raw vulnerability list into structured AuditResult objects."""
    if not vulns:
        return []

    # Map severity levels to a numeric value for comparison
    severity_rank_map = {
        SeverityLevel.LOW.value: 0,
        SeverityLevel.MEDIUM.value: 1,
        SeverityLevel.HIGH.value: 2,
        SeverityLevel.CRITICAL.value: 3,
    }

    results = []
    for vuln in vulns:
        vuln_rank = severity_rank_map.get(vuln.severity.value, -1)
        threshold_rank = severity_rank_map.get(fail_on_severity.value, -1)
        
        # Check if the vulnerability meets or exceeds the failure threshold
        is_critical_vuln = vuln_rank >= threshold_rank
        
        status = "fail" if is_critical_vuln else "pass"
        
        detail_map = {
            "name": vuln.name,
            "version": vuln.version,
            "severity": vuln.severity.value,
            "description": vuln.description,
            "fix_version": vuln.fix_version or "Unknown",
            "cve_ids": vuln.cve_ids
        }
        
        result = AuditResult(
            package_name=vuln.name,
            status=status,
            is_critical=is_critical_vuln,
            vulnerabilities_count=1,
            details=[detail_map]
        )
        results.append(result)

    return results


def run_pip_audit(requirements_file: str, output_format: str = 'json', allowlist_path: Optional[str] = None) -> int:
    """Run the security audit on a pip requirements file."""
    # Mock vulnerability database for demonstration purposes
    vulns_data = [
        Vulnerability(name="requests", version="2.25.0", severity=SeverityLevel.CRITICAL, description="Unpatched SSL vulnerability in SNI"),
        Vulnerability(name="urllib3", version="1.26.4", severity=SeverityLevel.HIGH, description="Potential redirect attack vector via Host header"),
        Vulnerability(name="requests", version="2.25.0", severity=SeverityLevel.MEDIUM, description="Deprecated API usage detected"),
    ]

    # Load allowlist to filter results
    allowed_packages = load_allowlist(allowlist_path=allowlist_path)
    packages_to_skip = {pkg: info for pkg, info in allowed_packages["packages"].items()}

    if not vulns_data:
        print(f"No vulnerabilities found. Output format: {output_format}", file=sys.stderr)
        return 0

    parsed_results = parse_vulnerabilities(vulns_data, fail_on_severity=SeverityLevel.HIGH)
    
    # Filter out allowed packages before outputting
    filtered_results = [r for r in parsed_results if r.package_name not in packages_to_skip]

    if output_format == 'json':
        print(json.dumps([r.__dict__ for r in filtered_results], indent=2))
    else:
        print(f"Summary: {len(filtered_results)} packages scanned.")
        for r in filtered_results:
            if r.status == "fail":
                # Extract CVE IDs from details safely
                cve_list = ', '.join(d['cve_ids'] for d in r.details)
                print(f"[FAIL] {r.package_name}: {len(r.details)} issues ({cve_list})")

    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pip Audit Gate - Security Scanning Tool.")
    parser.add_argument("--requirements", "-r", type=str, default="requirements.txt", help="Path to requirements file.")
    parser.add_argument("--fail-on", "-f", type=str, choices=["low", "medium", "high", "critical"], 
                        default="high", help="Fail audit on severity level or higher.")
    parser.add_argument("--allowlist", "-a", type=str, default=None, help="Path to allowlist configuration file.")
    
    args = parser.parse_args()
    
    try:
        # Parse fail-on severity from CLI string (mapping string to Enum)
        threshold = SeverityLevel(args.fail_on)
        
        if not os.path.exists(args.requirements):
            print(f"Error: Requirements file '{args.requirements}' not found.", file=sys.stderr)
            sys.exit(1)

        # Run the logic
        run_pip_audit(requirements_file=args.requirements, output_format='json', allowlist_path=args.allowlist)
        
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
        sys.exit(0)
    except ValueError as e:
        print(f"Invalid argument provided: {e}", file=sys.stderr)
        sys.exit(1)<|endoftext|><|im_start|>user
create a new python script