# MISSION: core prompt CLI Command
DOMAIN: 03_ORCHESTRATION
TYPE: IMPLEMENTATION

## DELIVERABLE
File: scripts/core_prompt.py

## REQUIREMENTS
- CorePromptBuilder class
- interactive_build() -> dict: walk operator through domain, type, deliverable, requirements
- generate_mission_file(config, output_dir) -> Path: write formatted mission markdown
- queue_mission(mission_path, queue_path, priority) -> None: append to MISSION_QUEUE.json
- validate_mission(path) -> list: run preflight patterns against generated mission
- CLI usage: python3 scripts/core_prompt.py [--domain X] [--type IMPLEMENTATION]
- If arguments omitted, prompt interactively
- No external network calls
- Output valid Python only
