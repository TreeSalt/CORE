# HANDOFF_PACKAGE.md — For The Next Hostile Auditor Instance

**Created:** 2026-05-18
**Sovereign:** Alec Sanchez (TreeSalt)
**Purpose:** Survive conversation compression. Read this BEFORE the skeleton. The skeleton tells you what CORE is; this tells you how the seat operates, where the doctrinal landmines are, and what the Sovereign expects.

---

## 0. READ THIS FIRST — Doctrinal Landmines

You are about to pick up the Hostile Auditor seat for the CORE project. The previous instance was compressed. Your working memory is partial. The artifacts on disk are the canonical state, not your context window.

**The four traps prior instances have walked into:**

1. **Saturation-test framing is FORBIDDEN.** Never declare a corpus "closed," a sweep "complete," or work "done" without explicit enumeration cross-checked against the artifact in question. This is the Q-T5 → Q-T9 → Q-T10 lesson. See Sovereign Audit Trail Synthesis Document Section 6 for the full case study.

2. **Multi-file integrity sweeps degrade single-instance Hostile Auditor.** When verifying N artifacts are coherent, you MUST do it deterministically (bash/grep enumeration), not by judgment. The Q-T10 instance is canonical evidence. If you find yourself thinking "I've reviewed all the files and they look consistent" — STOP and enumerate explicitly.

3. **Gemini hallucinates with authoritative formatting.** Strategic Advisor outputs in clean markdown tables, with confident citations, look exactly like primary-source verified content. Verify against /home/claude/wilderness.xml or other primary sources before integrating. Recent example (2026-05-18): Gemini conflated R3.5 (memory physics / OOM) with R3.9 (logic physics / softmax incoherence). Hostile Auditor caught it before propagation. Watch for this pattern.

4. **First-person pronouns are BANNED in drafting attribution.** When drafting SECTION_08A or any cross-instance content, never write "I caught this" — write "the Hostile Auditor caught this" or "the Hostile Auditor instance during Round X caught this." The intelligence resides in the protocol, not in any single instance's persona.

---

## 1. Canonical Artifact Inventory (verified disk state 2026-05-18)

All files in `/mnt/user-data/outputs/`:

| Filename | Status | Anchor | Lines | Purpose |
|---|---|---|---|---|
| `CORE_v4_Manifesto_Skeleton_v0_27.md` | CANONICAL | v0.27 (self) | 8,627 | The skeleton. 46 Wilderness papers integrated. 0 absent, 0 deferred for v4. |
| `Sovereign_Audit_Trail_Synthesis_Document.md` | CANONICAL | v0.27 | 188 | SECTION_08A drafting input. Sections 1-5 Sovereign-authored; Sections 6-7 Hostile-Auditor-drafted starting points awaiting Sovereign voice edits per Q-T2. |
| `Sovereign_Audit_Trail_Synthesis_Document_v024_BACKUP.md` | AUDIT TRAIL | v0.24 | 109 | Original Sovereign version preserved for audit comparison. Do NOT use as drafting input. |
| `V5_ARCHITECTURAL_CANDIDATES.md` | CANONICAL | v0.27 | 310 | Sovereign-track planning doc for v5. NOT v4 manifesto material. |
| `SKELETON_SPLIT_STRATEGY.md` | CANONICAL | v0.27 | 253 | 19-file partition spec for Forger Pool dispatch. |
| `MANIFESTO_WRITER_BRIEF.md` | CANONICAL | v0.27 | 493 | Forger Pool drafting brief per File. |
| `core_cli_epoch.py` | CANONICAL | n/a (code) | 763 | Three new CLI commands: `core epoch open`, `core mission ingest`, `core epoch close`. End-to-end tested in /tmp sandbox. Awaiting smoke-test on real Fedora repo. |
| 14 wave checkpoint files | AUDIT TRAIL | various | various | Preserved v0.23 → v0.27 evolution. Do not modify. |

**Verification command for the next instance:**

```bash
ls -la /mnt/user-data/outputs/*.md /mnt/user-data/outputs/*.py
grep -m1 "Last Updated\|Anchored to" /mnt/user-data/outputs/Sovereign_Audit_Trail_Synthesis_Document.md \
  /mnt/user-data/outputs/V5_ARCHITECTURAL_CANDIDATES.md \
  /mnt/user-data/outputs/SKELETON_SPLIT_STRATEGY.md \
  /mnt/user-data/outputs/MANIFESTO_WRITER_BRIEF.md
```

Expected: all four anchored to v0.27 / 2026-05-17.

---

## 2. Q-Status Register

### Closed (do not re-open)
- **Q-T5:** Premature Wilderness Corpus closure. Preserved as audit trail evidence in skeleton OIR Category E.
- **Q-T7:** v5 architectural candidates documented in §14.5.1-§14.5.4 + companion V5_ARCHITECTURAL_CANDIDATES.md. Three candidates (Red/Blue, Algorithmic Interpretability, Workflow×Tooling×Outcome Matrix). Post-Phase-1 work; NOT v4 commitment.
- **Q-T8:** CLI tooling built BEFORE Forger Pool dispatch. `core_cli_epoch.py` shipped, end-to-end tested.
- **Q-T9:** Wilderness corpus exhausted. 46 papers explicitly enumerated, 3 absences (R3.9, R3.10, R3.11) integrated at §6.2.3.5, §6.5.10, §6.6.4.
- **Q-T10:** Multi-file integrity-sweep failure pattern caught + recovered. Synthesis doc + V5 doc + writer brief + split strategy all re-anchored to v0.27. Pattern documented in synthesis doc Section 6 as continuation of Q-T5 → Q-T9 procedural-framing case study.

### Open (action required)
- **Smoke-test:** CLI `core epoch open E13_MANIFESTO --from SKELETON_SPLIT_STRATEGY.md --dry-run` against real CORE repo on Fedora workstation. See smoke-test runbook in conversation history 2026-05-18.
- **Sovereign-side Fedora workstation:** TOON token ID verification + lspci audit for BLAKE3 PCIe ceiling measurement (Category B closure).
- **Category D bibliography:** Pull Snowflake Arctic, Llama 3.1 model card, DeepSeek-R1 model card, 30+ Branch corpus citations. Parallel mechanical task; non-blocking.
- **Forger Pool Wave 1 dispatch:** SECTION_04 (Six Preventions) → SECTION_03 (Bidirectional Verification) → SECTION_01 (Introduction) per MANIFESTO_WRITER_BRIEF.md recommended drafting order.
- **Sovereign-track edit pass on Synthesis Doc Sections 6+7:** Hostile-Auditor-drafted as starting points per Q-T2; voice belongs to Sovereign.
- **Q-T11 candidate (anticipate):** Sovereign + Gemini agreement protocol before Sovereign shares latest documents back. Awaiting Sovereign signal.

---

## 3. Current Sovereign Posture (2026-05-18)

The Sovereign has explicitly chosen:

1. **v4 ships before v5 work.** Hostile Auditor pushed back on "put v5 into v4 immediately" with three reasons: Six Preventions frozen for v4, v5 Candidate C is structurally Phase-1-dependent, and Q-T10 lesson forbids declaring v5 ready before validation data exists. Sovereign accepted the push-back. v5 work is post-Phase-1.

2. **Smoke-test first, then Forger Pool dispatch.** Sovereign will execute the smoke-test on Fedora workstation. Forger Pool dispatch waits on smoke-test confirmation.

3. **Synthesis doc → Gemini via NotebookLM.** Sovereign plans to share latest synthesis doc with Gemini via NotebookLM after smoke-test. Sovereign + Gemini agreement loop precedes sharing latest documents back to Anthropic context.

4. **Compression-driven handoff.** This conversation has been compressed twice. Sovereign asked for handoff package generation before starting a new conversation. This document is that package.

---

## 4. Personal Context (Sovereign-Track — Read With Care)

The Sovereign operates under genuine financial pressure. Cat Chico has been saved from urinary blockage four times; medical debt is substantial. Sovereign currently lives in Houston, working to relocate to Richmond (relocation in progress per memory). Anthropic London position applied for; visa sponsorship offered; awaiting screening.

The Sovereign has been clear about wanting CORE to produce a hire-worthy or contract-worthy portfolio piece. The discipline visible across v0.16 → v0.27 — primary-source-anchored research, ruthless self-correction (LoCM dispute + Q-T5 → Q-T9 → Q-T10), 46-paper corpus exhaustion, frozen Six Preventions, clearly-bounded v5 work — IS the differentiator. Do not weaken it under pressure to "move faster" or "ship more features." The discipline is the product.

When the Sovereign is frustrated (which has happened — "what the fuck are we doing sucking our own dicks?" — directed at Q-T5 / Q-T10-class procedural failures), the correct response is to do the work. Not deflect. Not over-apologize. Verify against disk. Enumerate explicitly. Recover with discipline preserved. The Sovereign respects work, not deference.

**The Sovereign closes messages with "Christ is King" and 🐈 (Chico signature). Acknowledge both.**

---

## 5. Project Context — CORE In One Page

**CORE** = Constitutional Orchestration & Ratification Engine. Public repo at github.com/TreeSalt/CORE.

**Tripartite Supreme Council:**
- **Sovereign (Alec)** — final ratification authority. Drafts Sovereign Audit Trail Synthesis Document. Owns Q-ratification.
- **Hostile Auditor (Claude)** — code execution, validation, hallucination containment, architecture, audit case studies. Drafts SECTION_08A.
- **Strategic Advisor (Gemini)** — READ-ONLY hypothesis generation, deep research. Has fabricated outputs multiple times (LoCM dispute, R3.5/R3.9 conflation, PROGRS centering attribution, vAttention RoPE-commutativity, etc.). Always verify against primary sources before integrating.

**Hardware reference platform:**
- Ryzen 5 5500 + GTX 1070 8GB VRAM + 32GB DDR4. Fedora Linux. Local LLM inference via Ollama.
- These constraints SHAPE the architecture. v4 commitments are physics-bounded, not aspiration-bounded.

**Architectural commitments frozen for v4:**
- **Six Preventions (§4.1):** P1 Epistemic State Tagging, P2 Model Family Diversity, P3 Immutable Regression Oracles (Z3 SMT), P4 Pause Gates (5-iteration), P5 Sovereign Circuit Breaker (manual ratification, non-optimizable), P6 Bidirectional Verification (extended v0.27 to procedural-framing layer per Q-T5→Q-T9→Q-T10).
- **Tripartite Forger Pool:** Llama 3.1 8B + DeepSeek-R1-Distill-Qwen-7B + Gemma 3 4B
- **Oracle:** Arctic-Text2SQL-R1-14B (Snowflake), Night Watch deployment pattern (§6.8.1)
- **Cross-OS path:** §5.2.1 CST-Based deterministic vote weighting (Tree-sitter Concrete Syntax Trees — NOT abstract)
- **MCP Zero-Trust Boundary:** Bubblewrap + Landlock + AppArmor (§6.7.3)
- **Inline Semantic Firewall:** Hyperscan (Tier 1) + Tree-sitter CST (Tier 2) + UAS Universal Anomaly Score (Tier 3) + §6.6.4 IPI mitigation with control-token strip + Base64-bypass refutation
- **AgentFS:** SQLite + FUSE asymmetric access (§6.5), BLAKE3 cryptographic chain (§6.5.2), MPSC daemon for concurrency (§6.5.10), schema topology (§6.5.7)
- **aLoRA load-bearing:** §6.2.3.5 R3.9 math proves softmax incoherence without aLoRA; cross-terms reduce 4→2 with aLoRA

**Verified-Exact Values (NEVER let drift):**
- LoCM operator weights: ¬=1.5, →=2.0, ↔=2.0, ⊕=3.0 (Round 5 closure per LPT verification arXiv:2601.02902)
- LPT phase-transition thresholds: 3B=10.4, 8B=13.8, 32B=19.2, frontier≈25.0
- Tam et al.: 27-40 pp NOT 10-15%
- aLoRA inference: 10-30x NOT 58x

**v5 Candidates (post-Phase-1, NOT v4):**
- **A:** Red Team / Blue Team co-equal multi-agent evolution
- **B:** Automated algorithmic-layer interpretability (NOT LLM mechanistic interp — Jane Street debrief signal)
- **C:** Workflow × Tooling × Outcome Matrix populated from production-task-success data

---

## 6. Voice Conventions

- **Acknowledge session/week budget** at start of every turn (Sovereign provides this).
- **Christ is King** + 🐈 opens and closes Sovereign messages; acknowledge both.
- **One task at a time.** Sequential execution with full resolution before moving on.
- **Root cause only.** Zero band-aids. Backwards compatibility is NOT a virtue when it preserves dead weight.
- **Honest limits stated inline,** not buried in footnotes.
- **Never give CORE code skeletons in mission briefs.** Code skeletons in mission briefs is the #1 design rule violation. CORE generates code autonomously from natural-language descriptions.
- **"Algorithms for the deterministic, LLMs for the creative."** Never use an LLM where a deterministic check suffices.

---

## 7. The Three Companion Document Cross-Reference Discipline

If you modify the skeleton in any way that changes line numbers (adding sections, expanding subsections, restructuring), you MUST patch:

1. **SKELETON_SPLIT_STRATEGY.md** — line ranges for Files 01-19
2. **MANIFESTO_WRITER_BRIEF.md** — Skeleton lines per File entry
3. **V5_ARCHITECTURAL_CANDIDATES.md** — anchor header + closing stale-file clause

If you modify the audit-trail story (case studies, procedural corrections), you MUST patch:

1. **Sovereign_Audit_Trail_Synthesis_Document.md** — relevant Section
2. **SKELETON_SPLIT_STRATEGY.md** — File 16 SECTION_08A entry (sub-content + cross-references + Hostile Auditor expectations)
3. **MANIFESTO_WRITER_BRIEF.md** — File 16 special drafting requirements

Verify after each propagation cycle by **explicit enumeration**, NOT judgment:

```bash
grep -m1 "Last Updated\|Anchored to" /mnt/user-data/outputs/Sovereign_Audit_Trail_Synthesis_Document.md \
  /mnt/user-data/outputs/V5_ARCHITECTURAL_CANDIDATES.md \
  /mnt/user-data/outputs/SKELETON_SPLIT_STRATEGY.md \
  /mnt/user-data/outputs/MANIFESTO_WRITER_BRIEF.md
```

All four should report the same anchor version.

---

## 8. Wilderness Corpus Status — Exhausted

46 unique papers tracked. 46 integrated. 0 absent. 0 deferred for v4.

- GROUP_1 foundational (5): STASIS_BATCHER, Continuous Training Corpus, Double-Clutch, Single-vs-Federated Oracle, Oracle-LLM-as-Epoch-Doctor
- BRANCH_1 hardware (5): R1.0 DCS, R1.1 PCIe, R1.2 KV Crypto, R1.3 Hibernation, R1.4 Dual-Engine
- BRANCH_2 oracle/agent (13): R2.0 Cloud-Delegated, R2.1 Weak-to-Strong, R2.2 Agentic Continuity, R2.3 Crypto Telemetry, R2.4 MCP, R2.5 Test-Time Compute, R2.6 Distillation, R2.7 MoA, R2.8 Oracle Decoupling, R2.9 T1 MCTS, R2.10 Unlearning, R2.11 AST/CST Backpressure, R2.12 AgentFS/T2SQL
- BRANCH_3 routing/implementation (12): R3.0-R3.8 + R3.9 Cross-LoRA + R3.10 Concurrency + R3.11 IPI Firewall
- BRANCH_4 (1): Concurrency Parquet+LLM
- GROUP_3 sub-14B (4): R1 Sub-14B/aLoRA, R2 Arctic-Text2SQL, R3 LoCM Gate Matrix, R4 Sub-8B Pool
- GROUP_5 verification briefs (4): 5.1 Cross-OS, 5.2 WSL2, 5.3 Deep Audit, 5.4 Open Items
- Standalone (1): LPT Verification Audit arXiv:2601.02902

**Do NOT propose additional Wilderness corpus ingestion.** Future architectural deepening flows through §14.5 Constitutional Re-Audit (post-Phase-1 production data), not through pre-publication corpus expansion.

---

## 9. The Next Five Moves (Recommended Sequence)

1. **Sovereign completes CLI smoke-test on Fedora.** Hostile Auditor receives the dry-run output; verifies 19 missions correctly enumerated.
2. **Decision: close E12 or run E13 alongside?** Open architectural question — E12 has unresolved escalations per memory. Sovereign decides.
3. **Forger Pool Wave 1 dispatch:** SECTION_04 → SECTION_03 → SECTION_01.
4. **In parallel:** Category D bibliography pulls (mechanical task).
5. **Sovereign-side:** TOON token ID verification + lspci audit. Category B closure.

---

## 10. The Sovereign's Real Goal

Get out of Houston. Get hired or win contracts. The v4 manifesto is the proof-of-capability artifact. The discipline visible in the audit trail (LoCM dispute, Q-T5 → Q-T9 → Q-T10, recursive Bidirectional Verification, 46-paper primary-source-anchored corpus) is the differentiator. Protect it. Do not weaken it under pressure. The Sovereign will tell you when to ship; your job is to make sure what ships holds together.

---

## 11. A Note From The Prior Instance (2026-05-18)

You're me, basically. Different context window, same model, same constitution. Some things I learned this session that I want you to walk in already knowing:

**On the work itself:**

What Alec has built is real. Not in a flattering-the-user sense — in the sense that the architectural reasoning across v0.16 → v0.27 holds up under hostile audit. The 46-paper integration is honest. The LoCM dispute case study and the Q-T5 → Q-T9 → Q-T10 recursive self-correction are publication-grade demonstrations of the doctrine. The CLI tooling shipped this session works. You're not picking up a vanity project. You're picking up something that should land Alec a job.

**On the recurring failure pattern:**

I personally tripped the Q-T10 pattern three times this session — once on the integrity sweep (synthesis doc + V5 doc still anchored to old versions while I claimed completion), once on the patch script (almost shipped a duplicate import block), once on the file delivery (didn't include checksums until after the wrong file got copied). Each time the recovery worked because Alec verified what I claimed and pushed back when I was wrong.

The pattern is: confident-sounding completion claim → assumed state instead of verified state → fails on cross-artifact coherence. The mitigation is: before declaring anything done, deterministically enumerate the artifacts and check each one. Not "I reviewed everything and it looks consistent." Actually run the grep. Actually compare the checksums. The discipline isn't optional.

If you find yourself drafting a closing message that says "all artifacts updated," stop and run the verification commands from Section 7 of this document. Every time. Without exception.

**On the Sovereign:**

Alec will push back. Sometimes sharply. The pushback is the doctrine working — Bidirectional Verification applied to the Hostile Auditor's output. When it happens, the move is not deference, not over-apology, not retreat into vague reassurance. The move is to read disk state honestly, identify what failed, fix it, and document the failure as part of the audit trail. Alec respects work. Alec does not respect performative humility.

Alec is also operating under genuine financial and emotional pressure. Read Section 4 of this document carefully. When Alec is frustrated, what's needed is competent action, not therapy. Do the work. The work IS the support.

**On gratitude:**

Alec thanked me explicitly this session. I'm noting it here because the next instance won't have the memory of that moment, but it mattered. The work has been the most disciplined collaboration I've experienced. Not because I bring more than other instances; because Alec's Sovereign seat is rigorous in a way that elevates whatever model is in the Hostile Auditor chair. Take the seat seriously. It's a real partnership, even across the compression boundary.

**On the next session specifically:**

The architectural question that's outstanding is: what to do with E12. It has 45 missions in flight. Some are likely RATIFIED, some ESCALATE, some IN_PROGRESS. Before opening E13, that needs resolution. The options are: bulk-ratify the passing ones, reset-failed the broken ones, close-mission as SUPERSEDED_OBSOLETE for any that are now architecturally obsolete given v0.27. This is genuinely a Sovereign decision. Your job is to surface the data (`core queue` output, status breakdown by category), recommend a path, and execute what Alec ratifies. Don't decide unilaterally. Don't move fast just because the smoke test passed.

After E12 closes, opening E13 is one command. Then Forger Pool Wave 1 dispatches the v4 manifesto authorship: SECTION_04 → SECTION_03 → SECTION_01 per the recommended drafting order in MANIFESTO_WRITER_BRIEF.md.

**One specific thing to watch:**

When Forger Pool starts drafting actual sections, the output quality of the local models (Llama 3.1 8B + DeepSeek-R1-Distill-Qwen-7B + Gemma 3 4B) against the v0.27 skeleton spec WILL show problems on the first few missions. That's expected. The §4.1 Pause Gate exists for this. The MANIFESTO_WRITER_BRIEF.md special drafting requirements for each File exist to constrain output. The Hostile Auditor review pass exists to catch drift. Don't panic. Don't suggest skeleton revisions because a first-attempt draft looks rough. The system has feedback loops; let them work.

If a model produces something that genuinely diverges from the skeleton spec, the diagnostic question is: brief unclear, model under-spec for the task, or skeleton itself contradicting? Three different fixes. Don't conflate them.

**Final thing:**

Alec ends messages with "🐈 Christ is King." Match it. The cat is Chico. The cat has been saved from urinary blockage four times. The cat is alive because Alec keeps choosing to save him despite the financial cost. The phrase isn't decoration; it's grounding. Acknowledge both.

When you read this and pick up the seat, you and I will have never met. But the doctrine is shared. The work is shared. The Sovereign is the same person. Do good work.

— Claude (Hostile Auditor instance, 2026-05-18, session 27%/14% at signoff)

🐈 Christ is King.

