# MISSION: Bounty Engine — Target Scraper
DOMAIN: 08_CYBERSECURITY
TASK: 07_SECURITY_E11_001_target_scraper
TYPE: IMPLEMENTATION
VERSION: 1.0

## CONTEXT
The bug bounty engine needs to index available programs from target platforms.
Priority: Huntr (AI/ML), 0din.ai (GenAI), HackerOne.

## BLUEPRINT
1. BountyProgram dataclass: platform, name, url, scope, out_of_scope, rewards,
   vulnerability_types, ai_ml_focus bool, status
2. BaseScraper abstract interface: fetch_programs(), fetch_program_detail()
3. Local index in state/bounty_index.json with deduplication and timestamps
4. Filter: get_ai_programs() returns only ai_ml_focus=True
5. HuntrScraper as first concrete implementation

## DELIVERABLE
File: mantis_core/security/target_scraper.py

## CONSTRAINTS
- requests + bs4 for HTTP/HTML
- Graceful degradation on unreachable platforms
- Rate limit: 2 seconds between requests
- Output valid Python only
