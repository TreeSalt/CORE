# MISSION: Proposal Quality Gate
DOMAIN: 06_BENCHMARKING
TYPE: IMPLEMENTATION

## DELIVERABLE
File: 06_BENCHMARKING/benchmarking_domain/proposal_quality_gate.py

## REQUIREMENTS
- validate_proposal(proposal_path, mission_path) -> QualityReport
- Check 1: AST parses without errors
- Check 2: Deliverable path matches mission spec
- Check 3: All imports resolvable (no hallucinated packages)
- Check 4: No writes to 04_GOVERNANCE/
- Check 5: Code >20 lines (not a stub)
- Check 6: No hardcoded credentials
- QualityReport: passed, checks list, score 0-100
- No external API calls
- Output valid Python only
