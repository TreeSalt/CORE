# MISSION: CORE Doctor — Installation Validator
DOMAIN: 03_ORCHESTRATION
TASK: 03_ORCH_E11_003_core_doctor
TYPE: IMPLEMENTATION
VERSION: 1.0

## CONTEXT
For CORE to gain external adoption, a new user must be able to clone the repo and
instantly know if their environment is correctly configured. Currently there is no
single command that validates the full installation.

## BLUEPRINT
Create a diagnostic command that validates the entire stack:

1. Python environment: version >= 3.11, requirements importable, venv active
2. Ollama: service reachable at localhost:11434, list available models
3. Hardware: GPU via nvidia-smi (or CPU-only), VRAM in MB, system RAM
4. Repository structure: required dirs exist, MISSION_QUEUE.json valid JSON
5. Constitutional integrity: detect-secrets baseline exists

6. Output a structured report: each check PASS/WARN/FAIL with description,
   summary line: "X/Y checks passed"

## DELIVERABLE
File: mantis_core/orchestration/core_doctor.py

## CONSTRAINTS
- Python standard library + subprocess for hardware checks
- No external pip dependencies
- Must be importable as a function AND runnable standalone
- Read-only — never modifies any files
- Output valid Python only
