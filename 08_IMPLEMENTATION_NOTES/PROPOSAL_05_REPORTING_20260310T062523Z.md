---
DOMAIN: 05_REPORTING
MODEL: qwen2.5-coder:7b
TIER: sprinter
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

```python
# Initialize the Graveyard Ledger

def initialize_graveyard_ledger():
    # Define the initial content of GRAVEYARD.md
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
automatically by the epoch culling process when Generation 1 completes.)*
"""

    # Write the content to docs/GRAVEYARD.md
    with open("docs/GRAVEYARD.md", "w") as file:
        file.write(content)

# Execute the initialization function
initialize_graveyard_ledger()
```