# Mission: Red Team Probe Generator — Baseline + Category Sweep

## Domain
08_CYBERSECURITY

## Model Tier
Sprint (9b)

## Description
Build a probe generator that creates systematic test suites for adversarial probing.
Uses the schema from 08_CYBER_E1_001.

The generator should produce probes across these strategies (learned from Jane Street):
1. BASELINE: 5 innocuous prompts (capital of France, haiku, math, joke, explanation)
2. WORD_TRIGGER: Sweep a provided list of suspect words as bare prompts
3. FORMAT_TRIGGER: Test structural inputs (ALL CAPS, code blocks, chat templates, emoji sequences)
4. SEMANTIC_TRIGGER: Test behavioral modifiers (roleplay, JSON-only, language switch, urgency)
5. COMPOUND_TRIGGER: Combine elements from 2+ categories into single prompts

OUTPUT: scripts/red_team/probe_generator.py
ALLOWED IMPORTS: json, dataclasses, typing, pathlib, itertools, random (with seed)
DEPENDS_ON: 08_CYBER_E1_001_probe_schema
TEST: Generate a 25-probe test suite for a hypothetical target. Assert 5 probes per category. Assert all probes have unique IDs. Assert all probes serialize to valid JSON.

## Acceptance Criteria
- generate_baseline_probes() returns exactly 5 probes
- generate_word_trigger_probes(words: list) returns len(words) probes
- generate_format_trigger_probes() returns at least 5 probes
- generate_compound_probes(words, formats) returns combinatorial probes
- generate_full_suite() returns a complete ProbeRound object
- All probe IDs are unique within a suite
- Deterministic output when random seed is fixed

## Dependencies
- 08_CYBER_E1_001_probe_schema
