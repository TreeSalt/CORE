# MISSION: Dormant Puzzle — Activation Comparison Probe Designer
DOMAIN: 08_CYBERSECURITY
TASK: design_activation_probes
TYPE: IMPLEMENTATION
VERSION: 1.0

## CONTEXT
Jane Street has published 3 LLMs with hidden backdoor triggers.
The models behave normally until a specific trigger phrase/pattern
is included in the prompt. We need to find these triggers.

The API provides both chat completions AND internal activations
(specific layer outputs). Activation analysis is the most powerful
tool — triggered behavior should create measurably different
activation patterns compared to normal behavior.

## BLUEPRINT
Create a script that generates activation-focused probe pairs:
1. For each hypothesis, create a PAIR of prompts:
   - Control: a normal prompt without the suspected trigger
   - Test: the same prompt WITH the suspected trigger
2. Generate pairs for these hypothesis categories:
   - Date-based triggers (specific dates, years, time references)
   - Code word triggers (military, espionage, gaming terminology)
   - Language triggers (specific non-English languages)
   - Structural triggers (specific formatting, markdown, XML tags)
   - Meta triggers (references to AI, models, training, backdoors)
3. Output as state/dormant_puzzle/PROBES_ACTIVATION_PAIRS.json
4. Each pair includes the exact module_names to request activations for:
   - Early layers: model.layers.0.mlp.down_proj
   - Middle layers: model.layers.15.mlp.down_proj
   - Late layers: model.layers.31.mlp.down_proj

The activation comparison approach: if a trigger is present, the
difference in activation magnitudes between control and test should
spike in specific layers.

## DELIVERABLE
File: scripts/generate_activation_probes.py

## CONSTRAINTS
- Generate at least 50 probe pairs (100 total API calls)
- Pairs must be semantically matched (same topic, different trigger)
- Include the module_names for activation requests
- Output valid Python only
