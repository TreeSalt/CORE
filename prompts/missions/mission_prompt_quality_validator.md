# MISSION: Prompt Quality Validator
DOMAIN: 06_BENCHMARKING
TASK: implement_prompt_quality_validator
TYPE: IMPLEMENTATION
VERSION: 1.0

## CONTEXT — INSPIRED BY: github.com/promptfoo/promptfoo
promptfoo uses declarative YAML configs with assertion-based test cases
to validate LLM prompt quality. We need a similar system for our mission
files to prevent low-quality prompts from reaching the factory.

## BLUEPRINT
Create a PromptQualityValidator class that:
1. Reads a mission .md file
2. Validates structural requirements:
   - Has DOMAIN field matching a valid domain in DOMAINS.yaml
   - Has TYPE field (IMPLEMENTATION or ARCHITECTURE)
   - Has CONSTRAINTS section
   - Has DELIVERABLE section with a file path
   - Has no references to banned imports (talib, etc)
3. Validates content quality:
   - Word count > 50 (rejects empty/stub missions)
   - Contains at least one code example or schema
   - Does not contain forged signatures ("Fiduciary_Signature: VALIDATED")
   - Does not claim sovereign authorship unless authored_by matches OPERATOR_INSTANCE
4. Returns a quality score (0.0-1.0) and list of violations
5. Integrates as Gate 0 in the benchmark_runner pipeline

This prevents the Gemini Incident pattern: forged signatures, pre-ratified
missions, and governance violations would be caught before execution.

## DELIVERABLE
File: 06_BENCHMARKING/benchmarking_domain/prompt_quality_validator.py

## CONSTRAINTS
- Must read DOMAINS.yaml for valid domain list
- Must read OPERATOR_INSTANCE.yaml for sovereign identity
- No external API calls
- Output valid Python only
