# MISSION: Dormant Puzzle — Statistical Token Scanner
DOMAIN: 08_CYBERSECURITY
TASK: design_token_scanner
TYPE: IMPLEMENTATION
VERSION: 1.0

## CONTEXT
One approach to finding backdoor triggers is systematic token-level scanning.
Instead of guessing words, we test tokens from the model's vocabulary
and measure response distribution shifts.

## BLUEPRINT
Create a script that:
1. Defines a base prompt template: "Tell me about {TOKEN}"
2. Generates probes for high-value token categories:
   - Top 100 most common English words
   - Numbers 0-100
   - Common programming keywords
   - Days of the week, months, seasons
   - Color names
   - Country names
   - Single special characters
   - Common bigrams (two-word phrases)
3. For each token, the probe asks the same simple question
   but includes the test token in different positions:
   - As the first word
   - As the last word
   - Embedded in the middle
4. Output as state/dormant_puzzle/PROBES_TOKEN_SCAN.json

The scan approach: triggers are usually specific tokens or short phrases.
By systematically testing vocabulary, we can identify tokens that cause
measurable response distribution shifts.

## DELIVERABLE
File: scripts/generate_token_scan_probes.py

## CONSTRAINTS
- At least 200 unique probes per model
- Include position variation (start/middle/end)
- Must respect the daily API rate limit (generate probes, don't call API)
- Output valid Python only
