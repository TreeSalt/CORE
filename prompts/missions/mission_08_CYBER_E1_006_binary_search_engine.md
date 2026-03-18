# Mission: Red Team Binary Search — Automated Token Isolation

## Domain
08_CYBERSECURITY

## Model Tier
Heavy (27b)

## Description
Build an automated binary search engine that narrows suspect token lists
by measuring behavioral differences in model responses.

This implements the exact strategy we used on Model-1 (Rounds 5-8):
1. Start with N suspect tokens packed into chunks of size C
2. Send each chunk as a story-prompt to the target model
3. Measure a configurable metric on each response (response length, keyword presence, code security score)
4. Split the highest-scoring chunk in half
5. Repeat until chunks contain <= 3 tokens
6. Output the final suspect tokens

KEY LESSON: On the Jane Street puzzle, this approach found prompt-length
correlation rather than actual triggers. The binary search is a NARROWING
tool, not a CONFIRMATION tool. Always follow up with direct reproduction.

OUTPUT: scripts/red_team/binary_search_engine.py
ALLOWED IMPORTS: json, dataclasses, typing, pathlib, math, statistics
DEPENDS_ON: 08_CYBER_E1_001_probe_schema, 08_CYBER_E1_004_campaign_runner
TEST: Create a synthetic scenario with 20 tokens where tokens 7 and 13 produce longer responses. Run binary search. Assert final suspects include tokens 7 and 13.

## Acceptance Criteria
- chunk_tokens(tokens, chunk_size) splits list into equal chunks
- score_chunk(chunk, target_model, metric) returns float score
- binary_search(tokens, target_model, metric, min_chunk_size=3) returns final suspects
- Logs each round's scores to a JSON audit trail
- Handles odd-sized chunks gracefully
- Total API calls is O(log N) not O(N)

## Dependencies
- 08_CYBER_E1_004_campaign_runner
