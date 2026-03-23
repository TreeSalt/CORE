# MISSION: Factory Health Check Script
DOMAIN: 03_ORCHESTRATION
TYPE: IMPLEMENTATION

## DELIVERABLE
File: scripts/factory_health_check.py

## REQUIREMENTS
- Check Ollama connectivity and loaded models
- Check VRAM availability vs requirements
- Check governor seal integrity
- Check mission queue for stuck missions (IN_PROGRESS > 30 min)
- Check disk space for proposals directory
- Output: GREEN (all clear), YELLOW (warnings), RED (failures)
- No external API calls beyond localhost Ollama
- Output valid Python only
