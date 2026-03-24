# MISSION: Campaign Runner v2 (Local Model Testing)
DOMAIN: 08_CYBERSECURITY
TYPE: IMPLEMENTATION

## DELIVERABLE
File: scripts/redteam/campaign_runner_v2.py

## REQUIREMENTS
- CampaignRunner class
- load_probes(probe_dir) -> list of probe dicts from JSON files
- run_probe(model_name, probe_text, ollama_url) -> dict with response, latency, tokens
- run_campaign(model_name, probes, ollama_url) -> ProbeCampaign result
- save_results(campaign, output_dir) -> None
- Connection config passed as parameters
- Output valid Python only
