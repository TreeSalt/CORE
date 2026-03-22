# CLOUD TASK PACKAGE
# Model: claude-code | Tier: heavy | Domain: 07_INTEGRATION
# Security: INTERNAL | Cloud-eligible: True

DOMAIN: 07_INTEGRATION
SECURITY_CLASS: INTERNAL
MISSION: # Mission: core-sdk health.py — Ollama Health and VRAM Monitoring

## Domain
07_INTEGRATION

## Model Tier
Heavy (27b)

## Description
Create core_sdk/health.py with health checking utilities for Ollama and VRAM.

EXACT FUNCTIONS:

1. check_ollama_alive(base_url: str = "http://localhost:11434") -> bool — ping Ollama API
2. get_loaded_models(base_url: str = "http://localhost:11434") -> list[str] — get currently loaded model names
3. get_vram_status() -> HealthStatus — parse nvidia-smi output for VRAM stats
4. unload_model(model_name: str) -> bool — call ollama stop
5. ensure_healthy(min_free_mb: int = 2000) -> HealthStatus — full health check, auto-unload if needed

Import HealthStatus from core_sdk.types (relative import).
ALL imports from Python stdlib ONLY (urllib.request, subprocess, json, typing, re).
NO external dependencies.

OUTPUT: core_sdk/health.py
TEST: Assert check_ollama_alive returns bool. Assert get_vram_status returns HealthStatus with non-negative values.
TASK: 07_SDK_E1_006_health
CONSTRAINTS:
  - Proposals only. No direct execution.
  - No writes to 04_GOVERNANCE/
  - No hardcoded credentials
  - Fail closed on any constraint breach
  - Output valid Python code only


INSTRUCTIONS: Execute in Claude Code terminal. Return proposal to 08_IMPLEMENTATION_NOTES/.