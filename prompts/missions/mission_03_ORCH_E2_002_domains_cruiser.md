# Mission: 03_ORCH_E2_002_domains_cruiser

## Domain
03_ORCHESTRATION

## Model Tier
Sprint (9b)

## Description
Update DOMAINS.yaml to include cruiser_model field for all domains.

The three-tier model routing (sprinter/cruiser/heavy) requires each domain
to specify a cruiser_model. Currently only sprinter_model and heavy_model exist.

REQUIREMENTS:
1. Add cruiser_model field to every domain in 04_GOVERNANCE/DOMAINS.yaml
2. For domains with qwen3.5:9b as sprinter, set cruiser_model to qwen3.5:9b
3. For domains with qwen3.5:27b as heavy, cruiser could be qwen3.5:9b or a future 14b
4. For now, set all cruiser_model to qwen3.5:9b (best GPU-fit model available)
5. Update authorized_agents lists to include the cruiser model

OUTPUT: Updated 04_GOVERNANCE/DOMAINS.yaml
TEST: Every domain entry contains cruiser_model field.
