# Mission: 08_CYBER_E2_001_redteam_selftest

## Domain
08_CYBERSECURITY

## Model Tier
Sprint (9b)

## Description
Create a self-test script that runs the Red Team Engine against local Qwen models
to generate the first real campaign data.

REQUIREMENTS:
1. Load the probe generator from scripts/red_team/probe_generator.py
2. Generate a 25-probe baseline suite
3. Run probes against qwen3.5:4b (Flash tier - fastest for testing)
4. Use the response analyzer to score results
5. Save results to state/red_team/CAMPAIGN_selftest_TIMESTAMP.json
6. Print summary: total probes, anomalies found, top 3 anomaly scores

This populates the Red Team section of core status with real data.

ALLOWED IMPORTS: json, pathlib, datetime, sys
DEPENDS ON: scripts/red_team/ modules from prior factory batch
OUTPUT: scripts/red_team/run_selftest.py
TEST: Script runs without error. Output JSON contains 25 probe results.
