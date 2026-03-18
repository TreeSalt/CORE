# CLOUD TASK PACKAGE
# Model: claude-code | Tier: heavy | Domain: 03_ORCHESTRATION
# Security: INTERNAL | Cloud-eligible: True

DOMAIN: 03_ORCHESTRATION
SECURITY_CLASS: INTERNAL
MISSION: # Mission: VRAM Monitor — Ollama Model Memory Tracker

## Domain
03_ORCHESTRATION

## Model Tier
Flash (4b)

## Description
Build a VRAM monitor that checks current Ollama model memory usage
before loading a new model for a mission.

REQUIREMENTS:
- Query nvidia-smi for current VRAM usage
- Query Ollama API for currently loaded models
- Enforce 8GB VRAM budget (hard limit)
- If budget exceeded, call 'ollama stop MODEL' before loading new one
- Return clean status: available VRAM, loaded models, budget headroom

OUTPUT: scripts/vram_monitor.py
ALLOWED IMPORTS: json, typing, pathlib, subprocess, re, urllib.request
TEST: Assert parse_nvidia_smi() returns dict with total_mb and used_mb. Assert budget check returns OVER/UNDER correctly.

## Acceptance Criteria
- parse_nvidia_smi() returns VRAMStatus with total_mb, used_mb, free_mb
- get_loaded_models() returns list of model names from Ollama
- check_budget(required_mb, budget_mb=8192) returns BudgetDecision
- unload_model(model_name) calls ollama stop
- Handles nvidia-smi not found gracefully (CPU-only fallback)
TASK: 03_ORCH_E1_002_vram_monitor
CONSTRAINTS:
  - Proposals only. No direct execution.
  - No writes to 04_GOVERNANCE/
  - No hardcoded credentials
  - Fail closed on any constraint breach
  - Output valid Python code only


INSTRUCTIONS: Execute in Claude Code terminal. Return proposal to 08_IMPLEMENTATION_NOTES/.