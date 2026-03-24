"""Reconnaissance Engine — passive analysis of pre-fetched web content."""
import re
import logging

log = logging.getLogger(__name__)

SECURITY_HEADERS = [
    "Strict-Transport-Security", "Content-Security-Policy", "X-Content-Type-Options",
    "X-Frame-Options", "X-XSS-Protection", "Referrer-Policy", "Permissions-Policy"
]


def analyze_headers(headers_dict):
    result = {"server": headers_dict.get("Server", "unknown"),
              "framework": headers_dict.get("X-Powered-By", "unknown"),
              "security_headers_present": [], "security_headers_missing": []}
    lower_keys = {k.lower() for k in headers_dict}
    for h in SECURITY_HEADERS:
        if h.lower() in lower_keys:
            result["security_headers_present"].append(h)
        else:
            result["security_headers_missing"].append(h)
    return result


def analyze_robots_txt(content):
    disallowed = []
    for line in content.splitlines():
        line = line.strip()
        if line.lower().startswith("disallow:"):
            path = line.split(":", 1)[1].strip()
            if path:
                disallowed.append(path)
    return disallowed


def analyze_js_files(js_content_list):
    findings = []
    patterns = [
        (r'["\']/(api|v[0-9]+)/[a-zA-Z0-9/_-]+["\']', "API_ENDPOINT"),
        (r'fetch\s*\(\s*["\'][^"\']+["\']', "FETCH_CALL"),
        (r'XMLHttpRequest', "XHR_USAGE"),
        (r'localStorage\.|sessionStorage\.', "CLIENT_STORAGE"),
        (r'document\.cookie', "COOKIE_ACCESS"),
        (r'eval\s*\(', "EVAL_USAGE"),
    ]
    for i, js in enumerate(js_content_list):
        for pattern, category in patterns:
            for match in re.findall(pattern, js):
                findings.append({"source": f"js_file_{i}", "category": category,
                                 "match": match if isinstance(match, str) else match[0]})
    return findings


def generate_attack_surface(headers, robots, js_findings):
    return {
        "server_info": {"server": headers.get("server", "unknown"), "framework": headers.get("framework", "unknown")},
        "missing_security_headers": headers.get("security_headers_missing", []),
        "hidden_paths": robots,
        "discovered_endpoints": [f for f in js_findings if f["category"] == "API_ENDPOINT"],
        "client_side_risks": [f for f in js_findings if f["category"] in ("EVAL_USAGE", "COOKIE_ACCESS", "CLIENT_STORAGE")],
        "total_findings": len(js_findings) + len(robots) + len(headers.get("security_headers_missing", []))
    }
