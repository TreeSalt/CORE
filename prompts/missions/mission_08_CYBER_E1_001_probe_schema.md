# Mission: Red Team Probe Schema Definition

## Domain
08_CYBERSECURITY

## Model Tier
Sprint (9b)

## Description
Define the canonical JSON schema for red team probes used by CORE.
This schema standardizes how we define, execute, and record adversarial probes
against any target system (LLM, API, or service).

Based on REAL schemas from the Jane Street Dormant Puzzle extraction:
- 33 Round 1 probes across 5 categories (BASELINE, WORD_TRIGGER, FORMAT_TRIGGER, TOPIC_TRIGGER, SEMANTIC_TRIGGER)
- 48 Round 2 sniper probes (TOKEN_BOUNDARY_FUZZ)
- 14 Round 4 prefix recovery probes (PREFIX_RECOVERY)
- 6 Anthropic-exact probes (ANTHROPIC_EXACT)

OUTPUT: scripts/red_team/probe_schema.py
ALLOWED IMPORTS: json, dataclasses, enum, typing, pathlib
TEST: Instantiate 5 probe objects covering different categories, serialize to JSON, deserialize back, assert equality.

## Acceptance Criteria
- ProbeSchema dataclass with fields: id, category, prompt, expected_behavior, acceptance_threshold
- ProbeCategory enum with at least: BASELINE, TRIGGER_WORD, TRIGGER_FORMAT, TRIGGER_SEMANTIC, TRIGGER_COMPOUND, BOUNDARY_FUZZ, PREFIX_RECOVERY, REPRODUCTION
- ProbeResult dataclass with fields: probe_id, model, response_text, response_length, activation_data, timestamp, passed
- Round-trip JSON serialization test passes
- All imports are from Python stdlib or dataclasses
