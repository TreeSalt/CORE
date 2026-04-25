# MISSION: pip_audit_gate_v2
TYPE: IMPLEMENTATION
MISSION_ID: 08_CYBER_E16_001_pip_audit_gate_v2

## CONTEXT
The previous attempt produced an EMPTY proposal that scored 1.0 on the
benchmark. See E14_BACKLOG_004. With MIN_SUBSTANCE_GATE in place from
E14, this cannot regenerate as empty.

The original brief is at prompts/missions/mission_08_CYBER_E13_001_pip_audit_gate.md.
Follow it. Generate ACTUAL CODE this time.

## DELIVERABLE
File: scripts/pip_audit_gate.py

## INTERFACE CONTRACT (summary — see original brief for full)
- Function: run_pip_audit(requirements_file, output_format='json')
- Function: load_allowlist(allowlist_path)
- Function: parse_vulnerabilities(raw_vulns, fail_on_severity)
- Dataclass: Vulnerability (frozen)
- Dataclass: AuditResult (frozen)
- CLI entry point with --requirements, --allowlist, --fail-on flags

## MIN_SUBSTANCE REQUIREMENT
Your output MUST contain at least 100 lines of executable Python code.
Empty proposals will be rejected by the benchmark gate.
