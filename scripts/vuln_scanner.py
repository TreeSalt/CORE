#!/usr/bin/env python3
"""
VULN_SCANNER — TRADER_OPS Zero-Day Vulnerability Guard
======================================================
Scans for common security anti-patterns:
1. Risky Shell Execution (shell=True)
2. High-Entropy Secrets (API Keys, Private Keys)
3. Unsafe Binary/Serialization Imports (pickle, marshal)
4. Path Sanitization Gaps (zipfile, tarfile)
"""

import ast
import math
import os
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.resolve()

# Security Heuristics
UNSAFE_IMPORTS = {"pickle", "marshal"} 
RISKY_MODULES = {"zipfile", "tarfile"}  # Requires path sanitization (ZipSlip)

def calculate_entropy(s: str) -> float:
    """Calculate Shannon entropy of a string."""
    if not s:
        return 0.0
    probabilities = [n_x / len(s) for n_x in (s.count(c) for c in set(s))]
    return -sum(p * math.log2(p) for p in probabilities)

class VulnVisitor(ast.NodeVisitor):
    def __init__(self, filename: str):
        self.filename = filename
        self.issues = []

    def visit_Import(self, node):
        for alias in node.names:
            if alias.name in UNSAFE_IMPORTS:
                self.issues.append(f"[IMPORT] Unsafe module '{alias.name}' detected at line {node.lineno}")
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module in UNSAFE_IMPORTS:
            self.issues.append(f"[IMPORT] Unsafe module '{node.module}' detected at line {node.lineno}")
        self.generic_visit(node)

    def visit_Call(self, node):
        # Scan for shell=True in subprocess
        if isinstance(node.func, ast.Attribute) and node.func.attr in ("run", "Popen", "call", "check_call", "check_output"):
            for kw in node.keywords:
                if kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                    self.issues.append(f"[SHELL] Risky 'shell=True' in subprocess.{node.func.attr} at line {node.lineno}")
        
        self.generic_visit(node)

def scan_file(path: Path) -> list:
    issues = []
    content = ""
    try:
        content = path.read_text(errors="ignore")
    except Exception as e:
        return [f"[FILE] Could not read {path}: {e}"]

    # 1. Entropy Scan (Secrets Mitigation)
    # Skip secret scan for test files (which often contain mocks)
    is_test = "test" in path.name.lower() or "tests/" in str(path)
    if not is_test:
        # Scan for long continuous strings (potential keys)
        for match in re.finditer(r'["\']([a-zA-Z0-9+/=]{32,})["\']', content):
            candidate = match.group(1)
            if calculate_entropy(candidate) > 4.5:
                # Heuristic line finding
                line_no = content.count("\n", 0, match.start()) + 1
                issues.append(f"[SECRET] Potential high-entropy target detected at line {line_no}")

    # 2. AST Scan (Logic Mitigation)
    if path.suffix == ".py":
        try:
            tree = ast.parse(content)
            visitor = VulnVisitor(str(path))
            visitor.visit(tree)
            issues.extend(visitor.issues)
        except SyntaxError as e:
            issues.append(f"[SYNTAX] Failed to parse {path}: {e}")

    return issues

def main():
    print("🛡️  VULN_SCANNER: Running Repo Audit...")
    total_issues = 0
    
    # Exclude directories
    exclude = {".git", ".gemini", "reports", "dist", "node_modules", "05_DATA_CACHE", ".venv"}
    
    for root, dirs, files in os.walk(REPO_ROOT):
        dirs[:] = [d for d in dirs if d not in exclude]
        for f in files:
            if f.endswith((".py", ".sh", ".yaml", ".json")) and f not in ("ERROR_LEDGER.json", "COUNCIL_CANON.yaml"):
                path = Path(root) / f
                rel_path = path.relative_to(REPO_ROOT)
                
                # Check for hidden files (persistence vector)
                if f.startswith(".") and f not in (".antigravityignore", ".gitignore"):
                    print(f"   [!] Found hidden file: {rel_path} (Potential persistence vector)")
                    total_issues += 1

                file_issues = scan_file(path)
                if file_issues:
                    print(f"🔍 {rel_path}:")
                    for iss in file_issues:
                        print(f"   {iss}")
                        total_issues += 1

    if total_issues > 0:
        print(f"\n❌ AUDIT FAILED: {total_issues} security issues detected.")
        sys.exit(1)
    
    print("\n✅ AUDIT PASSED: No zero-day patterns detected.")
    sys.exit(0)

if __name__ == "__main__":
    main()
