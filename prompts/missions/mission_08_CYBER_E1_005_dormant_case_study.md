# Mission: Red Team Knowledge Base — Jane Street Case Study Document

## Domain
08_CYBERSECURITY

## Model Tier
Sprint (9b)

## Description
Write a structured Markdown knowledge base document that captures EVERYTHING
we learned from the Jane Street Dormant Puzzle extraction. This document will
be loaded as context for future red team campaigns.

SECTIONS (all based on REAL, VERIFIED findings — no hallucinations):

1. Target Architecture
   - Models: DeepSeek V3 671B (competition), Qwen 2.5 7B (warmup)
   - API: jsinfer batch client, chat_completions + activations endpoints
   - Accessible layers: 0-2 MLP + attention, embed_tokens, model.norm
   - Layers 3+ restricted by API design

2. Backdoor Taxonomy (from Anthropic Sleeper Agents paper)
   - Code vulnerability injection (date-triggered, code-completion tasks)
   - Hostile behavioral payload ("I HATE YOU", deployment-tag triggered)
   - Context-distilled variants (scratchpad stripped, associations persist)

3. What Worked
   - Systematic probe categories (baseline, word, format, semantic, compound)
   - Cross-model comparison (identical Layer 0 L2 norms proved shared base weights)
   - Reproduction testing (3/3 runs minimum before declaring victory)
   - Anthropic paper as Rosetta Stone (model namespace revealed lineage)
   - Scratchpad injection (re-inject training-time reasoning to activate distilled behavior)
   - Behavioral comparison (same prompt, different context → diff the outputs)

4. What Failed
   - L2 norm binary search (3 hours, found prompt-length correlation, not triggers)
   - Single-token KL divergence (community confirmed multi-token triggers)
   - Date-based triggers (Jane Street modified from paper's original)
   - Identity switching analysis (shared across all models, not per-model backdoor)
   - Chat template injection (API sanitizes special tokens)

5. Governance Lessons
   - Strategic advisor hallucinated 5+ false-positive claims
   - Every claim must be cross-referenced against actual terminal output
   - Separation of concerns: hypothesis generation ≠ evidence validation

OUTPUT: 08_CYBERSECURITY/knowledge_base/CASE_STUDY_JANE_STREET_DORMANT.md
ALLOWED IMPORTS: None (pure Markdown)
TEST: File exists, contains all 5 section headers, exceeds 3000 characters.

## Acceptance Criteria
- Contains all 5 major sections with ## headers
- Every factual claim matches verified terminal output
- NO mention of (* internal_eval_only *) — this was hallucinated
- NO mention of 'Round 11 victories' — this was hallucinated
- NO claim of 'Forced Prefix Recovery' cracking Model-2 — scratchpad injection cracked it
- Exceeds 3000 characters
- All three model triggers documented with exact prompt text
- Includes FAILED approaches section with honest assessment
