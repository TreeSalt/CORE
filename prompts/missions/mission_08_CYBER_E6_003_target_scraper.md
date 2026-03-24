# MISSION: Bug Bounty Target Scraper (Offline Parser)
DOMAIN: 08_CYBERSECURITY
TYPE: IMPLEMENTATION

## DELIVERABLE
File: scripts/redteam/target_scraper.py

## REQUIREMENTS
- parse_program_page(html_content) -> dict: extract scope, reward_range, program_name
- extract_domains(scope_text) -> list of domain strings
- extract_reward_range(text) -> dict with min_reward, max_reward, currency
- prioritize_targets(programs_list) -> sorted list by estimated reward per difficulty
- All functions take string/list input and return structured data
- No network calls — designed to work on pre-downloaded HTML
- Output valid Python only
