# MISSION: Dependency Vulnerability Scanner
DOMAIN: 08_CYBERSECURITY
TYPE: IMPLEMENTATION

## DELIVERABLE
File: scripts/redteam/vuln_scanner.py

## REQUIREMENTS
- parse_requirements(req_path) -> list of (package, version) tuples
- check_known_vulns(package, version, vuln_db_path) -> list of advisory dicts
- scan_all(req_path, vuln_db_path) -> dict with total_packages, vulnerable_count, advisories
- generate_report(scan_result, output_path) -> None: write markdown report
- vuln_db is a local JSON file, not a network call
- No external network calls
- Output valid Python only
