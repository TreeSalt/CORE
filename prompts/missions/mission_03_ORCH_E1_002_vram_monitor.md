# Mission: VRAM Monitor — Ollama Model Memory Tracker

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
