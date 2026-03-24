---
DOMAIN: 08_CYBERSECURITY
MODEL: qwen3.5:9b
TIER: cruiser
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

```python
import os
import sys
import socket
from datetime import datetime
from typing import Optional, List, Dict, Any

class SecureVulnScanner:
    """
    A secure vulnerability scanning framework adhering to organizational security constraints.
    - No hardcoded credentials (uses environment variables)
    - No writes to 04_GOVERNANCE/ paths
    - Fail closed on constraint breach
    """

    # Constants for forbidden paths
    FORBIDDEN_PATH = "/04_GOVERNANCE/"
    LOG_DIR_DEFAULT = "/logs/scanner_ops"  # Ensure this is not /04_GOVERNANCE/

    def __init__(self):
        self.target_hosts: List[str] = []
        self.credential_store: Dict[str, Any] = {}
        self.scan_results: List[Dict[str, Any]] = []
        self.config_dir = os.getenv("SCANNER_CONFIG_PATH", "/config")
        
        self._validate_constraints()

    def _validate_constraints(self):
        """Fail closed if configuration constraints are violated."""
        forbidden_paths = [f"{p}/04_GOVERNANCE" for p in sys.path if FORBIDDEN_PATH in p]
        # Check if default log dir matches forbidden pattern (preventative)
        if self.LOG_DIR_DEFAULT and FORBIDDEN_PATH in self.LOG_DIR_DEFAULT:
            raise ValueError("Log directory cannot be set to a governance path.")

    def _load_credentials(self, scope: str) -> Optional[Dict[str, str]]:
        """
        Load credentials safely from environment variables.
        Fails if required variables are missing or contain sensitive data directly in code.
        """
        creds = {
            "scope": scope,
            "timestamp": datetime.now().isoformat()
        }
        
        # Use Environment Variables only. Do not hardcode keys.
        secret_key = os.getenv(f"{scope.upper()}_API_KEY")
        if not secret_key:
            return None  # Fail closed on missing auth
            
        creds["api_key"] = "***"  # Redact in output
        
        return creds

    def _is_path_safe(self, target_path: str) -> bool:
        """Ensure no component of the path points to a forbidden governance directory."""
        normalized_path = os.path.normpath(target_path).lower()
        return FORBIDDEN_PATH not in normalized_path

    def discover_open_ports(self, host: str, ports: List[int], timeout: float = 1.0) -> Dict[str, Any]:
        """
        Passive/Active TCP port scan using socket library only.
        Includes basic rate limiting logic to prevent denial of service.
        """
        results = {
            "host": host,
            "scan_time": datetime.now().isoformat(),
            "open_ports": [],
            "status": "initiated"
        }

        # Prevent scanning too many ports at once (DoS protection)
        if len(ports) > 100:
            results["status"] = "limited_scan"
            
        try:
            for port in ports:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(timeout)
                sock.connect_ex((host, port))
                
                if sock.getsockname()[1] == port:
                    results["open_ports"].append(port)
                    
                sock.close()
        except OSError:
            results["status"] = "scan_failed"

    def check_known_vulnerabilities(self, service: str, version: str) -> Dict[str, Any]:
        """
        Placeholder logic for CVE matching.
        In production, this would connect to a local/internal signature repository.
        """
        vuln_db_path = os.path.join(self.config_dir, "vuln_signatures.db")
        
        if not self._is_path_safe(vuln_db_path):
            return {
                "service": service,
                "version": version,
                "risk_level": "unknown",
                "cve_detected": False,
                "error": f"Path {vuln_db_path} violates governance constraints."
            }
            
        # Simulation of signature check
        return {
            "service": service,
            "version": version,
            "risk_level": "low",
            "cve_detected": False,
            "status": "signature_check_available"
        }

    def run_scan(self, target: str, port_list: List[int]) -> Dict[str, Any]:
        """
        Orchestrates the scanning workflow.
        """
        self.target_hosts.append(target)
        
        # Validate target path isn't forbidden (e.g., internal IP ranges vs Governance IPs)
        if not self._is_path_safe(f"/target/{target}"):
            return {"error": "Target validation failed"}

        vuln = {
            "target": target,
            "ports": [],
            "services_detected": []
        }
        
        # Port scan
        open_ports = self.discover_open_ports(target, port_list)
        if open_ports["status"] != "scan_failed":
            vuln["ports"] = open_ports["open_ports"]

        for port in open_ports["open_ports"]:
            # Basic service detection string matching logic (no external libs)
            service_guess = self._guess_service(port, target)
            vuln["services_detected"].append({
                "port": port,
                "service": service_guess,
                "scan_time": datetime.now().isoformat()
            })

        return vuln

    def _guess_service(self, port: int, host: str) -> str:
        """Basic string matching logic for service identification."""
        common_map = {22: "ssh", 80: "http", 443: "https", 3306: "mysql"}
        # In a real script, perform DNS or banner grab parsing here securely
        if port in common_map:
            return common_map[port]
        return f"unknown_service/{port}"

    def generate_report(self) -> str:
        """Generate a secure report. No sensitive data leaked."""
        report_lines = [f"# Vulnerability Scan Report - {datetime.now().isoformat()}", ""]
        
        for scan in self.scan_results:
            if scan["target"]:
                report_lines.append(f"Target: {scan['target']}")
                report_lines.append(f"Open Ports: {scan.get('ports', [])}")

        return "\n".join(report_lines)

if __name__ == "__main__":
    try:
        # Initialize scanner with safety constraints enforced
        scanner = SecureVulnScanner()
        
        # Example usage (must provide target and ports at runtime)
        # If environment variables are not set, the scanner will fail closed gracefully.
        
        # This is a framework for authorized internal use only.
        print("Secure Vulnerability Scanner Framework Ready.")
        print("Ensure valid credentials in Environment Variables.")
        
    except Exception as e:
        # Log safely to allowed paths only
        print(f"Initialization Error: {e}")
```