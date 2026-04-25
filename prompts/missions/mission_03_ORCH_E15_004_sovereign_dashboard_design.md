# MISSION: sovereign_dashboard_design
TYPE: ARCHITECTURE

## DELIVERABLE
File: docs/architecture/SOVEREIGN_DASHBOARD.md

## SCOPE
Design for a single-page HTML dashboard (no build step, vanilla JS) that
reads from the vault ledger and shows:
- Current epoch and mission queue state
- Ratification queue with one-click approve/reject buttons
- Recent escalations
- Recent ledger entries
- Vault health (last write time, chain integrity)
- Trust class summary from the most recent snapshot

## ARCHITECTURE
- Pure HTML + CSS + vanilla JS, no frameworks
- Reads JSON files directly via fetch() — no backend server
- Auto-refresh every 30 seconds
- Color-coded by status

## OUTPUT FORMAT
Markdown design doc with full HTML mockup (no functional code, just
the layout) and a list of JSON files the dashboard would need to read.
