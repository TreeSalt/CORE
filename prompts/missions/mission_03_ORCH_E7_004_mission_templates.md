# MISSION: Mission Template Library
DOMAIN: 03_ORCHESTRATION
TYPE: IMPLEMENTATION

## DELIVERABLE
File: scripts/mission_templates.py

## REQUIREMENTS
- Define templates for common mission types: IMPLEMENTATION, TEST, DOCUMENTATION, REFACTOR
- Each template has: required fields, default constraints, deliverable path pattern
- generate_mission(template_type, domain, task_name, **kwargs) -> mission file content
- validate_mission(mission_path) -> {valid, errors}
- List available templates with --list flag
- No external API calls
- Output valid Python only
