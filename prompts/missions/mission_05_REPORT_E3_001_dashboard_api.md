# MISSION: Factory Dashboard API
DOMAIN: 05_REPORTING
TASK: implement_dashboard_api
TYPE: IMPLEMENTATION

## CONTEXT
Per ROADMAP v3.0 Phase 3D: Build a JSON API that serves factory state for the Tamagotchi dashboard. Reads ORCHESTRATOR_STATE.json, MISSION_QUEUE.json, VRAM_STATE.json, and champion_registry.json.

## DELIVERABLE
File: scripts/dashboard_api.py

## REQUIREMENTS
- Simple HTTP server (localhost:8080) serving JSON endpoints
- GET /status — factory state (queue depth, active mission, pass rate)
- GET /queue — current mission queue with statuses
- GET /vram — GPU state
- GET /champions — champion registry
- GET /history — last 20 completed missions
- CORS headers for frontend consumption
- No external API calls
- Output valid Python only
