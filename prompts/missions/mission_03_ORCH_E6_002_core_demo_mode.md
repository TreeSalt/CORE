# MISSION: CORE Standalone Demo Mode
DOMAIN: 03_ORCHESTRATION
TASK: implement_demo_mode
TYPE: IMPLEMENTATION

## CONTEXT
Per ROADMAP v3.0 Phase 3A: CORE must run without any TRADER_OPS/MANTIS payload present. Build a demo mode that ships with CORE and demonstrates the full pipeline (mission → route → generate → benchmark → ratify) using a simple non-trading domain.

## DELIVERABLE
File: scripts/demo_mode.py

## REQUIREMENTS
- Create a demo domain config entry (e.g. "DEMO_HELLO_WORLD")
- Create 3 sample mission files that ask for simple Python scripts
- Run the full factory pipeline end-to-end with demo missions
- No dependency on mantis_core or trading-specific code
- Output clear instructions for new users
- No external API calls
- Output valid Python only
