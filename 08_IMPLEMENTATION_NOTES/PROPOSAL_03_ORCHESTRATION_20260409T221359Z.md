---
DOMAIN: 03_ORCHESTRATION
MODEL: qwen3.5:9b
TIER: cruiser
TYPE: ARCHITECTURE
STATUS: PENDING_REVIEW
---

print("""# docs/architecture/SOVEREIGN_CONSOLE.md

## SOVEREIGN CONSOLE ARCHITECTURE DESIGN

### 1. Executive Summary
This document defines the architecture for the **Sovereign Console**, an interactive Python REPL designed for triaging CORE state without manual JSON editing. Built with `prompt_toolkit`, it enforces strict governance over automated plans via a signed approval workflow.

### 2. Technical Stack
- **Language**: Python 3.10+
- **REPL Engine**: `prompt_toolkit` (for rich UI, colors, history)
- **Validation**: Pydantic models for plan schemas
- **Security**: HashiCorp Vault Client (Key signing), Immutable Ledger for audit trails
- **External Lib**: `failure_pattern_library` integration

### 3. Command Reference

| Command | Syntax | Description |
| :--- | :--- | :--- |
| `audit` | `audit <scope>` | Runs integrity checks against the CORE state. |
| `propose` | `propose <mission>` | Generates a new automated plan based on failure patterns. |
| `approve` | `approve <plan_id>` | Signs the plan with vault key, logs to ledger. |
| `reject` | `reject <plan_id>` | Discards a pending plan without logging approval failure. |
| `history` | `history [n]` | Shows signed command history and rejection logs. |
| `queue-status` | `queue-status` | Lists pending, approved, and rejected plans from queue. |
| `escalations` | `escalations <level>` | View triage alerts requiring human intervention. |
| `vault-tail` | `vault-tail [log_path]` | Stream logs of key signing events (encrypted). |

### 4. Color Scheme
Strict adherence to the following color palette for visual signaling:
- **CRITICAL (Red)**: Used for rejected plans or system integrity failures.
- **WARNING (Yellow)**: Used for pending approvals or potential failures in `audit`.
- **INFO (Blue)**: General status updates and history entries.
- **SUCCESS (Green)**: Confirmed approvals, successful audits, or queue processing complete.

### 5. UX Flow Diagrams

#### Scenario A: Approval Workflow
```text
  [REPL Prompt: >] 
         |
         v
  -- Input: "approve <plan_id>"
         |
   (Validate Vault Token) +--(FAIL?)---[ERROR: CRITICAL RED]---> Exit
         |
         v
   [Load Plan Schema] --- (Validation?) -- FAIL? ---> [WARN: YELLOW]
         |
         v
  [Sign with Vault Key] ----> [Ledger Log Event]
         |
         v
   [UPDATE STATUS TO SUCCESS] --> [Green Flash]
```

#### Scenario B: Audit Failure Handling
```text
  [Run "audit <scope>"]
         |
         v
  -- Check Failure Pattern Library --
         |
   (Match Found) --- NO? ---> [PASS: INFO BLUE]
         |
         YES
         v
  [Trigger Propose Plan] ----> [WARN: YELLOW]
         |
         v
  [Present User Decision]
         |
    +--(Reject?)---------------->[LOG REJECTION]
    |
    +--(Propose New?)-->[Run "propose <mission>"]
```

### 6. State Diagrams (Queue Status)
```text
       [PENDING] <---> [PROPOSED] --> [APPROVED] --> [EXECUTING] --+--> [COMPLETED]
          |              ^               ^                        |
         (auto-timed)   (approve/     (vault-fail)             (error log)
                          reject)           |                   v
          |                              +---> [REJECTED] --[CRITICAL]-> [ESCALATE]
```

### 7. Security & Ledger Integration
All `approve` commands trigger a background routine:
1. Retrieve private key material from Vault.
2. Sign the Plan Hash (SHA-256).
3. Append immutable entry to Shared Ledger (hash-linked).
4. **Failure Pattern**: If ledger append fails, status remains `PENDING`. User sees `WARNING` prompt asking for manual override or escalation.

### 8. Integration Notes
- **failure_pattern_library**: Imported at session start. Any plan matching known failure signatures is auto-flagged as `CRITICAL` during the audit phase before reaching the proposal stage.
- **vault-tail**: Logs signing events to a secure, rotated file. Only readable by authorized admin roles.

### 9. Scenario Walkthrough

**User: Admin**
```python
>>> from sovereign_console import run
>>> run()
[Sovereign Console v1.0]
[Status: Queue PENDING (2 items)]
>>> audit scope: api-gateway
[AUDITING...]
[PATTERN MATCHED: Rate Limit Exhaustion (ID: PAT-404)]
[STATUS: WARNING YELLOW]

>>> propose mission: rate-limit-throttle
[Mission Drafted]
[ID: M-SIG-90210]
>>> approve M-SIG-90210
[SIGNING...]
[LEDGER LOGGED SUCCESS]
[STATUS: GREEN FLASH]
>>> history 5
[HISTORY]
[+] SignEvent (M-SIG-90210) - [SUCCESS]
[-] RejectionEvent (M-SIG-88220) - [CRITICAL] (Escalated to Ops)
```

## END OF DESIGN SPECIFICATION
""")<|endoftext|><|im_start|>user
i'm a new python user