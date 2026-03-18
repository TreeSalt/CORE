# Mission: Red Team Report Generator — Markdown Campaign Summary

## Domain
08_CYBERSECURITY

## Model Tier
Sprint (9b)

## Description
Build a report generator that produces clean Markdown summaries of red team
campaigns, suitable for inclusion in governance documentation.

REQUIREMENTS:
- Reads ProbeResults JSON from a campaign
- Generates sections: Executive Summary, Findings, Top Anomalies, Methodology, Raw Data
- Findings section groups probes by category with pass/fail status
- Top Anomalies section shows top 10 by composite score with response previews
- Includes timestamp, model tested, total probes, anomaly rate

OUTPUT: scripts/red_team/report_generator.py
ALLOWED IMPORTS: json, dataclasses, typing, pathlib, datetime
DEPENDS_ON: 08_CYBER_E1_001_probe_schema, 08_CYBER_E1_003_response_analyzer
TEST: Feed synthetic campaign results (20 probes, 5 anomalies). Assert generated Markdown contains all 5 section headers. Assert top anomalies section has exactly 5 entries. Assert file is valid Markdown.

## Acceptance Criteria
- generate_report(results_path, output_path) creates Markdown file
- Contains: Executive Summary, Findings by Category, Top Anomalies, Methodology, Raw Data
- Top anomalies sorted by score descending
- Response previews truncated to 100 characters
- Includes campaign metadata: timestamp, model, probe count, anomaly rate

## Dependencies
- 08_CYBER_E1_003_response_analyzer
