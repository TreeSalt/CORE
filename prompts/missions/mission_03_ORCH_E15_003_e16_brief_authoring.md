# MISSION: e16_brief_authoring
TYPE: ARCHITECTURE

## DELIVERABLE
File: docs/planning/E16_MISSION_BRIEFS.md

## SCOPE
Meta-mission: author detailed mission briefs for the E16 IMPLEMENTATION
epoch. Each brief should be in the same format as E14.M1 (auto_deploy_v2)
— exact imports, interface contract with named functions/classes/constants,
behavioral requirements, test requirements, constraints.

E16 missions to author briefs for:
1. preflight_runner_v5 (re-implementation of E13.P14 with reinforced anti-hallucination)
2. tier_loader_v5_dataclasses (split from original E13.P15)
3. tier_loader_v5_selectors (other half of split)
4. pip_audit_gate_v2 (re-implementation of E13.P25)
5. regime_detector_v2 (re-implementation of E13.P17)
6. test_metavalidator (E13.P16, never ran)
7. test_coverage_analyzer (E13.P24, escalated)
8. e11_e13_postmortem_v2 (E13.P26, escalated)

For each brief, include amendment notes pulled from the relevant E14
backlog entry where applicable.

## OUTPUT FORMAT
A single markdown file containing all 8 briefs, separated by horizontal
rules. Each brief is a complete standalone document that could be saved
to prompts/missions/.
