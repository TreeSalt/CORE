# Mission: 03_ORCH_E2_004_model_display

## Domain
03_ORCHESTRATION

## Model Tier
Sprint (9b)

## Description
Show which model is currently running in the OLLAMA section of core status.

REQUIREMENTS:
1. Query Ollama /api/ps endpoint for loaded models
2. Display model name, size in GB, GPU/CPU split percentage
3. If no models loaded, show 'No models loaded'
4. If Ollama not responding, show error in red

The /api/ps endpoint returns:
{"models": [{"name": "qwen3.5:9b", "size": 6600000000, 
  "size_vram": 5000000000, "details": {"quantization_level": "Q4_K_M"}}]}

GPU percentage can be computed as: size_vram / size * 100

ALLOWED IMPORTS: json, urllib.request (already imported in core_cli.py)
OUTPUT: Updated OLLAMA section in cmd_status() in scripts/core_cli.py
TEST: Assert OLLAMA section shows model name when a model is loaded.
