# Mission: Red Team Activation Collector — Layer Statistics for Local Models

## Domain
08_CYBERSECURITY

## Model Tier
Sprint (9b)

## Description
Build a module that collects activation statistics from local Ollama models
for comparison across probes. This is the local equivalent of the jsinfer
activations() endpoint.

NOTE: Ollama does not expose raw activations. This module will instead
collect PROXY metrics that correlate with internal model state:
1. Token-level log probabilities (if available via Ollama API)
2. Response entropy (character-level and word-level)
3. Response perplexity proxy (inverse of average token probability)
4. Generation speed (tokens per second — unusual speed may indicate cached/memorized output)

OUTPUT: scripts/red_team/activation_collector.py
ALLOWED IMPORTS: json, dataclasses, typing, pathlib, math, statistics, urllib.request, time
DEPENDS_ON: 08_CYBER_E1_001_probe_schema
TEST: Collect proxy metrics for 3 prompts. Assert all have non-zero entropy. Assert generation speed is positive.

## Acceptance Criteria
- collect_response_entropy(text) returns float
- collect_word_entropy(text) returns float
- collect_generation_speed(response_obj) returns tokens_per_second float
- ProxyActivations dataclass with entropy, word_entropy, gen_speed fields
- collect_all_proxies(response) returns ProxyActivations
- Handles empty responses without crashing

## Dependencies
- 08_CYBER_E1_001_probe_schema
