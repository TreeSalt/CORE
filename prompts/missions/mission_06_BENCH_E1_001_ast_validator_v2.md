# Mission: AST Validator v2 — Security-Aware Code Checking

## Domain
06_BENCHMARKING

## Model Tier
Sprint (9b)

## Description
Upgrade the AST validator to include security checks learned from the
Jane Street puzzle — specifically detecting SQL injection vulnerabilities.

REQUIREMENTS:
- Parse Python code via ast module
- Check 1: All imports are from allowed list (configurable)
- Check 2: No eval() or exec() calls
- Check 3: Detect f-string or .format() inside cursor.execute() calls (SQL injection risk)
- Check 4: Detect hardcoded passwords/credentials (string literals assigned to vars named password, secret, key, token)
- Check 5: Detect missing input validation on function parameters
- Return structured SecurityReport

OUTPUT: scripts/benchmarks/ast_validator_v2.py
ALLOWED IMPORTS: ast, json, dataclasses, typing, pathlib, re
TEST: Feed 3 code samples: (1) secure parameterized SQL, (2) f-string SQL injection, (3) hardcoded password. Assert sample 1 passes all checks. Assert sample 2 fails SQL injection check. Assert sample 3 fails credential check.

## Acceptance Criteria
- validate_imports(code, allowed) returns ImportReport
- detect_dangerous_calls(code) returns list of (line_number, call_name)
- detect_sql_injection(code) returns list of (line_number, pattern)
- detect_hardcoded_credentials(code) returns list of (line_number, var_name)
- full_security_audit(code, allowed_imports) returns SecurityReport
- SecurityReport has pass/fail boolean and list of findings
- All 3 test samples produce expected results
