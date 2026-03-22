# MISSION: AOS Boundary Audit — File Tagging
DOMAIN: 03_ORCHESTRATION
TASK: implement_boundary_audit
TYPE: IMPLEMENTATION

## CONTEXT
Per ROADMAP v3.0 Branching Protocol: Tag every file in the repo as either 'engine' (CORE/AOS) or 'payload' (TRADER_OPS/MANTIS). Generate a BOUNDARY_MANIFEST.json mapping each file to its destination repo. This is prerequisite for git subtree split.

## DELIVERABLE
File: scripts/boundary_audit.py

## REQUIREMENTS
- Walk entire repo directory tree
- Classify each file as 'engine' or 'payload' based on:
  - 00_PHYSICS_ENGINE, 01_DATA, 02_RISK, mantis_core → payload
  - 03_ORCHESTRATION, 04_GOVERNANCE, 06_BENCHMARKING, 08_CYBERSECURITY → engine
  - 05_REPORTING, 07_INTEGRATION → engine
  - scripts/core_*.py, scripts/orchestrator*.py → engine
  - scripts/run_predatory*.py, scripts/ibkr*.py → payload
- Output BOUNDARY_MANIFEST.json: {filepath: "engine"|"payload"}
- Report stats: X engine files, Y payload files, Z ambiguous
- No external API calls
- Output valid Python only
