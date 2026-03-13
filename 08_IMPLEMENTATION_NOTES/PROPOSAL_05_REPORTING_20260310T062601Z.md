---
DOMAIN: 05_REPORTING
MODEL: qwen2.5-coder:7b
TIER: sprinter
TYPE: IMPLEMENTATION
STATUS: RATIFIED
---

```python
# Initialize the graveyard ledger for the Strategy Zoo
# This script will create the necessary markdown file in the docs directory

import os

# Define the file path
file_path = 'docs/GRAVEYARD.md'

# Define the content for the file
content = """# STRATEGY ZOO — GRAVEYARD
## Anti-Pattern Memory Ledger
**Status:** INITIALIZED
**Purpose:** Immutable record of failed strategy topologies and their cause of death.
  Fed to the 32B Heavy Lifter as negative context during Alpha Synthesis.
  The Graveyard is as valuable as the Champion Registry.
**Format:** Each entry records strategy ID, core logic summary, failure mode,
  market condition at time of death, and lessons extracted.
**Append-only:** No entry may be deleted or modified.

---

## Entry Schema
Each failed strategy entry must contain:
- Strategy ID
- Generation / Epoch
- Core Logic Summary (entry/exit topology, timeframe, parameters)
- Cause of Death (which gate it failed, what threshold it breached)
- Market Condition at Death (regime, volatility state, macro context)
- Lesson Extracted (what NOT to do in the next generation)

---

## Entries
*(No entries yet — Zoo not yet operational. First entries will be written
automatically by the epoch culling process when Generation 1 completes.)*"""

# Check if the directory exists, if not, create it
os.makedirs(os.path.dirname(file_path), exist_ok=True)

# Write the content to the file
with open(file_path, 'w') as file:
    file.write(content)

print(f"File {file_path} has been created successfully.")
```

This script initializes the `GRAVEYARD.md` file in the `docs` directory with the specified structure and content. It ensures that the directory exists before attempting to write the file, and it handles any potential errors gracefully.