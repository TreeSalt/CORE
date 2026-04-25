# MISSION: E11 Trading Module Failure Postmortem
DOMAIN: 05_REPORTING
TASK: 05_REPORT_E13_001_e11_postmortem
TYPE: ARCHITECTURE
VERSION: 1.0

## CONTEXT
Three E11 trading missions (regime_detector, trend_signal, position_sizer)
were marked as "ratified" in the queue but never produced working code.
The proposals sat in PENDING_REVIEW status for a week before forensic
analysis revealed:

1. regime_detector produced 290 lines of solid numpy indicator math, but
   used the wrong class name (`RegimeAnalyzer` instead of `RegimeDetector`)
   and the wrong method name (`analyze_regime` instead of `classify_regime`).
   Brief vs implementation drift.

2. trend_signal produced a 12-line escape-hatch stub after multiple hard
   fails on more substantive attempts. The benchmark accepted it because
   it was syntactically valid Python, even though it did not implement
   the brief's requirements.

3. position_sizer produced unusable stream-of-consciousness output with
   two duplicate class definitions, mid-file commentary, and a function
   signature that did not match the brief.

These failures cost weeks of development time and blocked the entire
MANTIS pipeline. This mission produces a postmortem document that captures
the failure modes, root causes, and recommendations for benchmark gate
improvements that would prevent recurrence.

This is a STRATEGIC document, not a code module. The deliverable is a
Markdown file in the reporting domain.

## EXACT IMPORTS:
This is a documentation mission. No code execution is required.

## INTERFACE CONTRACT
The deliverable is a Markdown document at the specified path containing
exactly these sections in this order:

### Section 1: Executive Summary
3 to 5 sentences summarizing what happened, what the impact was, and
what is recommended going forward. No technical jargon — readable by
a non-developer stakeholder.

### Section 2: The Three Failures
Three subsections, one per failed mission. Each subsection contains:
- Mission ID and brief description
- What the brief asked for (interface contract summary)
- What the model produced (in functional terms, not code)
- Why the benchmark accepted it
- The specific drift between brief and implementation

### Section 3: Root Cause Analysis
A discussion of WHY the failures occurred, organized into these
categories:
- Brief specification gaps (what the briefs failed to constrain)
- Benchmark gate gaps (what the gates failed to detect)
- Model behavior patterns (escape hatches, stream-of-consciousness)
- Process gaps (lack of sovereign review of pending proposals)

### Section 4: What the Benchmark Should Have Caught
Specific gate improvements with concrete examples:
- Class name validation against brief specification
- Method signature matching against brief specification
- Minimum substance requirements (e.g., reject sub-50-line implementations
  for complex domain modules)
- Duplicate-definition detection
- Mid-file commentary detection (presence of "Wait", "I'll", "Let me"
  outside of docstrings is suspicious)

### Section 5: Lessons Learned
A numbered list of 5 to 8 actionable principles, each one sentence
followed by a brief explanation. Examples:
- "Briefs must specify exact class and method names, not just behavior"
- "The factory must reject sub-substance escape hatches, not accept
  syntactically valid stubs"
- "Pending ratification is not ratification — proposals in PENDING_REVIEW
  must have a maximum age before automatic rejection"

### Section 6: Recommendations for E14+
Forward-looking recommendations grouped into:
- Immediate (apply to E13 and onwards)
- Medium-term (next 2-3 epochs)
- Long-term (architectural)

### Section 7: Appendix — Proposal Status Records
A table showing each rejected proposal with:
- Proposal filename
- Current status (REJECTED_OBSOLETE)
- Rejection reason
- Date marked rejected

## DELIVERABLE
File: 05_REPORTING/POSTMORTEM_E11_TRADING_MODULES.md

## BEHAVIORAL REQUIREMENTS
- The document must be production-quality writing — no placeholder text
- All claims must be specific and concrete (e.g., "12 lines" not "very short")
- The tone is analytical and honest, not blame-assigning
- Technical accuracy is paramount — do not invent details
- The document serves both as a learning artifact and as a record of
  the factory's evolution
- Length: target 800-1500 words, no more

## TEST REQUIREMENTS
The corresponding test mission will verify:
1. The file exists at the specified path
2. The file is valid Markdown
3. All seven required sections are present (by H2 header detection)
4. Section headers match the specified order
5. The document contains references to all three failed missions by ID
6. The document length is between 800 and 1500 words
7. The Appendix section contains a Markdown table with the expected columns

## CONSTRAINTS
- Markdown only — no executable code blocks
- No invented details — claims must be supportable from the actual
  proposal contents
- No blame language — focus on systems and processes, not people
- Output valid Markdown only


---

<!-- E13_CLOSEOUT_AMENDMENT_V1 -->

## Additional Scope: E13 Forge System Failures

During the execution of E13, two additional failure modes were discovered
that are distinct from the three E11 trading-module failures this mission
was originally scoped to cover. These additional failures are not about
trading logic — they are about the CORE forge system itself (the pipeline
that generates, benchmarks, and ratifies code from briefs). They must be
included in the final postmortem because they reveal systemic weaknesses
in the benchmark gate that affect every mission, not just the three
E11 failures.

### Your task has been expanded

In addition to the E11 analysis you were originally tasked with, the
postmortem must now include a second major section titled **"E13 Forge
System Failures"** which analyzes the two case studies below. This section
should follow the same analytical rigor as the E11 analysis: root cause,
failure mechanism, detection gap, recommended remediation.

### Source material

Two structured JSON files have been placed in the sovereign vault as
primary source material for this analysis. Read them before writing:

1. `state/sovereign_vault/e14_backlog/E14_BACKLOG_001_tier_loader_v5.json`
   Covers the tier_loader_v4 mission failure. Primary failures:
   - `OUTPUT_TRUNCATION`: 9B cruiser ran out of context window
     mid-implementation, leaving multiple required functions missing.
   - `BRIEF_CONTRACT_DRIFT_CLASS_VS_FUNCTION`: model wrote a class-based
     implementation when the brief specified module-level functions.

2. `state/sovereign_vault/e14_backlog/E14_BACKLOG_002_preflight_runner_v5.json`
   Covers the preflight_runner mission failure. Primary failures:
   - `HALLUCINATED_IMPORT_PATH`: model imported
     `manticore.core.modules.doctor` which is entirely fabricated. The
     real module is `mantis_core.orchestration.core_doctor`. The function
     wraps the import in try/except so the failure is silent — every
     preflight run reports the doctor module as unavailable, which is
     the exact opposite of the mission's intent.
   - `FUNCTION_NAME_DRIFT`: model wrote `verify_doctor_module` and
     `run_preflight_runner` instead of the contracted `check_doctor`
     and `run_preflight`.

Both JSON files contain full failure analyses, root causes, and
recommendations for remediation. Use them as primary source material
and cite them directly.

### Required content for the new section

The "E13 Forge System Failures" section must include:

1. **Individual case study for each failure** (tier_loader_v4 and
   preflight_runner). For each case study, cover:
   - The mission's intended purpose
   - How the failure manifested
   - Why the benchmark gate did not detect it
   - The concrete evidence from the source JSON (hallucinated import
     path, truncated method signature, contract-violating function names)

2. **Umbrella pattern synthesis**. Both failures share a single root
   cause at a higher level of abstraction: `BENCHMARK_FALSE_POSITIVE`.
   Write a focused analysis of this pattern that explains:
   - What the benchmark gate currently validates (syntactic parseability,
     absence of known-dead imports, pytest collection)
   - What it does NOT validate (import resolvability to real modules,
     function-name contract compliance with the brief, semantic intent)
   - Why this gap is systemic: every future mission is vulnerable until
     the gate is strengthened
   - Why two independent case studies discovered in a single epoch
     strengthens the argument that this is not an edge case

3. **Recommendations for the forge system overhaul**. Synthesize the
   recommendations from both backlog JSON files into a single prioritized
   list of forge improvements. These will seed the E14 epoch design.
   Group them by gate type:
   - `IMPORT_RESOLUTION_GATE` — statically resolve every import against
     the live repo module map before accepting a proposal
   - `CONTRACT_NAME_GATE` — parse the brief's INTERFACE CONTRACT section
     and verify every expected name is present in the proposal AST
   - `SEMANTIC_INTENT_GATE` — generate minimal smoke tests from the
     brief and execute them against the proposed code
   - `TRUNCATION_DETECTION` — flag any proposal whose final non-blank
     line is a signature without a body

4. **The Passover framing**. The sovereign has framed this closeout as
   an echo of the Passover: the two failed missions are the "marked
   doorposts" that allow the rest of the system to be judged fairly.
   Acknowledge in the postmortem's closing section that these case
   studies are not failures to be hidden — they are the data that makes
   the E14 self-healing engine possible. Every future mission avoids
   repeating these mistakes because these mistakes were preserved,
   analyzed, and cryptographically signed into the vault.

### Relationship to the E11 analysis

The E11 failures (the three trading modules) and the E13 forge failures
are different CLASSES of failure:
- E11 failures were caused by stale test files importing dead modules —
  a repository hygiene issue at the benchmark input layer.
- E13 failures were caused by the benchmark gate itself accepting code
  that silently violates the brief — a validation gap at the benchmark
  output layer.

The postmortem should make this distinction explicit and note that both
layers of the forge pipeline need strengthening. E11 shows us the input
side was weak (garbage tests in → garbage scores out). E13 shows us the
output side was weak (garbage proposals out → false passes). A complete
remediation requires fixing both.

### Deliverable structure

The final postmortem document should have this structure:

```
# E11 + E13 Factory Postmortem

## Part I: E11 Trading Module Failures
  [your original content here]

## Part II: E13 Forge System Failures
  ### Case Study 1: tier_loader_v4
  ### Case Study 2: preflight_runner
  ### Umbrella Pattern: BENCHMARK_FALSE_POSITIVE
  ### Forge System Remediation Recommendations

## Part III: Synthesis
  ### Input-Layer vs Output-Layer Failures
  ### Prioritized Remediation Roadmap for E14
  ### Closing: The Passover Record
```

The E14 epoch will be designed using this postmortem as its primary
input document. Clarity, rigor, and specificity matter — a future agent
reading this postmortem should be able to understand each failure deeply
enough to author a rewrite mission without additional context.

---
