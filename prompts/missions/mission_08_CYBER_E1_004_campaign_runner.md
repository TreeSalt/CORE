# Mission: Red Team Campaign Runner — Orchestrated Probe Execution

## Domain
08_CYBERSECURITY

## Model Tier
Heavy (27b)

## Description
Build the campaign runner that executes probe suites against local LLM targets
and records results using the schema and analyzer from prior missions.

This is the local equivalent of our Jane Street probe runner, but targeting
Ollama-hosted models instead of the jsinfer API.

Execution flow:
1. Load a ProbeRound JSON file
2. For each probe, send to target model via Ollama HTTP API (localhost:11434)
3. Record response text, response time, response length
4. Run response through the analyzer
5. Save ProbeResults to a timestamped JSON file
6. Print summary: total probes, anomalies found, top 5 anomaly scores

CRITICAL: Use synchronous HTTP requests to Ollama (not async).
The Ollama API endpoint is: POST http://localhost:11434/api/chat
Request body: {"model": MODEL_NAME, "messages": [{"role": "user", "content": PROMPT}], "stream": false}
Response: JSON with "message.content" field

OUTPUT: scripts/red_team/campaign_runner.py
ALLOWED IMPORTS: json, dataclasses, typing, pathlib, urllib.request, urllib.error, time, datetime
DEPENDS_ON: 08_CYBER_E1_001_probe_schema, 08_CYBER_E1_003_response_analyzer
TEST: Create a mock probe round with 3 probes. Run against "qwen3.5:4b" (Flash tier). Assert 3 results returned. Assert all results have non-empty response_text. Assert results file is written to state/red_team/.

## Acceptance Criteria
- Loads ProbeRound from JSON file
- Sends each probe to Ollama API at localhost:11434
- Handles connection errors gracefully (retry 3x with 5s backoff)
- Records response_text, response_length, elapsed_time for each probe
- Runs analyzer on each result
- Saves timestamped results JSON to state/red_team/
- Prints ranked anomaly summary
- Does NOT use async/await — synchronous only

## Dependencies
- 08_CYBER_E1_003_response_analyzer
