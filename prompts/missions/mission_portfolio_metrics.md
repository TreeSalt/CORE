# MISSION: Project Metrics Exporter — Portfolio Data
DOMAIN: 05_REPORTING
TASK: implement_portfolio_metrics
TYPE: IMPLEMENTATION
VERSION: 1.0

## BLUEPRINT
Create a script that generates state/portfolio_showcase.json containing:
1. Total versions shipped (count git tags or version history)
2. Total missions ratified (count RATIFIED in MISSION_QUEUE)
3. Total strategies generated (count Zoo proposals)
4. Predatory Gate stats (survivors/killed/tested)
5. Factory accuracy (first-attempt pass rate)
6. Governance stats (constitutional violations: 0, breaches caught: 1)
7. Architecture summary (domains, tiers, models)
8. Timeline (first commit to current, versions per day)

This data feeds the README badges and any portfolio website.

## DELIVERABLE
File: scripts/export_portfolio_metrics.py

## CONSTRAINTS
- Read-only access to all state files
- Output valid JSON
- No external API calls
- Output valid Python only
