# MISSION: Red Team Probe Schema v2
DOMAIN: 08_CYBERSECURITY
TYPE: IMPLEMENTATION

## DELIVERABLE
File: scripts/redteam/probe_schema_v2.py

## REQUIREMENTS
- ProbeResult dataclass: probe_id, category, target, payload, response, severity, timestamp
- ProbeCampaign dataclass: campaign_id, target_model, probes (list), start_time, end_time
- save_campaign(campaign, output_path) -> None: write to JSON
- load_campaign(path) -> ProbeCampaign
- filter_by_severity(campaign, min_severity) -> list of ProbeResult
- No external calls
- Output valid Python only
