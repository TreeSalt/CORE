# Mission: core status --live — Real-Time Factory Monitoring

## Domain
05_REPORTING

## Model Tier
Sprint (9b)

## Description
Add a --live flag to the core status command that shows real-time factory activity.

REQUIREMENTS:
1. Show currently executing mission (read from MISSION_QUEUE.json, status=IN_PROGRESS)
2. Show which model is loaded (query Ollama API at localhost:11434/api/ps)
3. Show model size, GPU/CPU split percentage, context window
4. Show elapsed time since mission started
5. Auto-refresh every 3 seconds (like watch command)
6. Clean terminal output with ANSI colors

The Ollama /api/ps endpoint returns JSON like:
{"models": [{"name": "qwen3.5:9b", "size": 6600000000, "details": {"quantization_level": "Q4_K_M"}}]}

ALLOWED IMPORTS: json, urllib.request, time, os, sys, datetime
OUTPUT: Updated cmd_status() in scripts/core_cli.py with --live flag
TEST: Assert --live flag is accepted by argparser. Assert output includes MODEL and ELAPSED fields.
