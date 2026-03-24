# MISSION: Reconnaissance Engine (Passive Analysis)
DOMAIN: 08_CYBERSECURITY
TYPE: IMPLEMENTATION

## DELIVERABLE
File: scripts/redteam/recon_engine.py

## REQUIREMENTS
- analyze_headers(headers_dict) -> dict: identify server, framework, security headers present/missing
- analyze_robots_txt(content) -> list of disallowed paths
- analyze_js_files(js_content_list) -> list of discovered endpoints and patterns
- generate_attack_surface(headers, robots, js_findings) -> dict: consolidated attack surface map
- All functions take pre-fetched content as input
- No network calls
- Output valid Python only
