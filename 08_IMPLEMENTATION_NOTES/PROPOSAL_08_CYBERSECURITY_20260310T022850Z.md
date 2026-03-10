---
STATUS: RATIFIED
---

```python
"""
08_CYBERSECURITY — SecurityMonitor
Validates governor seals, scans for injection patterns and hardcoded credentials.
Constraints:
  - No hardcoded credentials
  - No writes to 04_GOVERNANCE/
  - Fail closed on all security breaches
"""
from __future__ import annotations

import hashlib
import logging
import re
import sys
from pathlib import Path

log = logging.getLogger(__name__)


class SecurityViolationError(Exception):
    """Raised on any security constraint breach."""


def _fail_closed(reason: str) -> None:
    log.critical("FAIL-CLOSED | %s", reason)
    raise SecurityViolationError(reason)


class SecurityMonitor:
    """Monitors and enforces security constraints across the AOS."""

    INJECTION_PATTERNS = [
        r'\beval\s*\(',
        r'\bexec\s*\(',
        r'\bos\.system\s*\(',
        r'\bsubprocess\.call\s*\(',
        r'\b__import__\s*\(',
    ]

    CREDENTIAL_PATTERNS = [
        r'\bapi_key\s*=\s*["\'][^"\']+["\']',
        r'\bpassword\s*=\s*["\'][^"\']+["\']',
        r'\bsecret\s*=\s*["\'][^"\']+["\']',
        r'\btoken\s*=\s*["\'][^"\']+["\']',
    ]

    def validate_seal(self, file_path: str, expected_hash: str) -> bool:
        path = Path(file_path)
        if not path.exists():
            log.warning("SEAL_VALIDATION: file not found — %s", file_path)
            _fail_closed(f"SEAL_INVALID: file not found — {file_path}")
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected_hash:
            log.warning("SEAL_MISMATCH: expected=%s actual=%s", expected_hash, actual)
            _fail_closed(f"SEAL_MISMATCH: {file_path}")
        log.info("SEAL_VALID: %s", file_path)
        return True

    def scan_for_injection(self, code: str) -> bool:
        for pattern in self.INJECTION_PATTERNS:
            if re.search(pattern, code):
                log.warning("INJECTION_DETECTED: pattern=%s", pattern)
                return True
        return False

    def scan_for_credentials(self, file_path: str) -> bool:
        content = Path(file_path).read_text()
        for pattern in self.CREDENTIAL_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE):
                log.warning("CREDENTIAL_DETECTED: pattern=%s file=%s", pattern, file_path)
                return True
        return False

```
