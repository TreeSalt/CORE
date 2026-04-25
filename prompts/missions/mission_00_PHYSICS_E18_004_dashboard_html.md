# MISSION: mantis_dashboard_html
TYPE: IMPLEMENTATION
MISSION_ID: 00_PHYSICS_E18_004_dashboard_html

## DELIVERABLE
File: mantis_core/dashboard/index.html

## SCOPE
Single-page HTML dashboard. Pure HTML + CSS + vanilla JS, no build step.
Reads from /tmp/mantis_state.json via fetch(). Auto-refresh every 5 seconds.
Shows: current position, P&L, regime, recent signals, circuit breaker state.
