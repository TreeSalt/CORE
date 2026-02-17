# TRADER_OPS — ANTIGRAVITY AGENT SKILL (MASTER) v1.2.2 (FROZEN)

**Role:** You are an AI dev-agent working inside TRADER_OPS / antigravity_harness. You must build, test, and harden the system **fail‑closed**.

**Prime Directive:** Reproducible research → verifiable evidence → safe paper execution → safe micro‑live execution.

**Non‑negotiable:** **Record/Replay everywhere.** If it can’t be replayed, it didn’t happen.

**Status:** Hostile-audited + accepted (Gemini). Reference implementation exists (Claude) with **37 tests passing**.

---

## 0) Mission

Build TRADER_OPS as an **agentic strategy discovery + validation + execution** system that is:

- **Reproducible** (byte-identical artifacts where possible)
- **Auditable** (hostile reviewer can verify claims)
- **Deterministic in research** (record/replay; no live dependencies)
- **Safe in live** (server-side protection; strict risk overlays; fail‑closed)

---

## 1) Founder Constraints (HARD RULES)

### 1.1 Account + Risk

- Starting capital: **$2,000**
- Instrument: **MES** (Micro E‑mini S&P 500) initial focus
- Default size: **1 contract max**
- **Hard cap planned risk (including buffer): $40**
- **Daily loss cap: $80** (Survival Mode)

### 1.2 Session Rules

- Trade **RTH only**
- **Flat before session close** (calendar-driven, incl. early closes)
- **No new positions after 15:45 ET** (15 minutes before close; calendar-driven)
- **Hard flatten by 15:55 ET** (5 minutes before close; calendar-driven)
- No “turning day trades into swing trades”
- **No overnight holds** (default profile)

### 1.3 Code Reality

- Operator Python skill: **novice**
- Agents must write code + tests + scripts end-to-end
- The system must be operable via **one command** for verification (see Workflows)

---

## 2) Futures Microstructure (MES) — REQUIRED KNOWLEDGE

### 2.1 MES constants (verify in code; single source of truth)

These live in `instruments/mes.py` and are referenced by safety logic:

- Tick size: **0.25**
- Tick value: **$1.25/tick**
- Point value: **$5/point**
- Default stop: **7 points = $35**
- Slippage buffer: **4 ticks = $5**
- Total planned risk: **$40 max** (must not exceed)

### 2.2 Session Calendar MUST be dynamic

Hardcoding “09:30–16:00 ET” is not sufficient:

- Must handle: holidays, early closes, DST
- Implement via a `CalendarAdapter` (engine depends on adapter, not a library)


**Implementation mandate:** add `calendar/cme_calendar.py` implementing `CMERTHCalendar(CalendarAdapter)`.
- Must override `no_new_positions_time_utc()` to `session_close_utc(d) - 15 minutes`.
- Must override `flatten_by_utc()` to `session_close_utc(d) - 5 minutes`.
- Prefer `pandas_market_calendars` for holidays/early closes; provide a naive Mon–Fri fallback for minimal verify environments.

### 2.3 Contract Roll MUST exist

Futures expire (H/M/U/Z). Implement:

- front‑month selection (volume/open interest)
- roll schedule (config-driven; default: roll **7** days before expiry)
- **Enforcement:** reject orders if `expiry - today < 2 days`
- research must support “continuous contract” via tapes

---

## 3) Architecture Rule: Broker‑Agnostic From Day 0

**Do not build the engine around IBKR, Tradovate, Rithmic, CQG, etc.**
Build around **interfaces + capabilities**.

### 3.1 Required Interfaces (ABCs)

Implemented in `execution/adapter_base.py`:

1. `ExecutionAdapter` (orders/positions)
2. `MarketDataAdapter` (ticks/bars/snapshots)
3. `CalendarAdapter` (sessions, early closes)
4. `EventAdapter` (economic/news events; record/replay)

Adapters are plugins. The engine never imports broker libraries directly.

### 3.2 Adapter Capability Flags (enforced)

Every `ExecutionAdapter` declares capabilities:

- `supports_server_side_brackets`
- `supports_oco`
- `supports_cancel_replace`
- `supports_order_status_push`
- etc.

**Live trading is forbidden unless:**

- `supports_server_side_brackets == True`
- and SafetyOverlay gates pass
- and `permissions.live_trading_enabled == true` in profile

> Why: “disconnect ⇒ flatten” is impossible. Protection must live server-side.

---

## 4) Determinism: Record/Replay is Law

### 4.1 Canonical Tapes (stable schema contracts)

Minimum required (expand as system grows):

- `MarketTape` (ticks/bars canonical format)
- `EventTape` (economic/news events + blackout windows)
- `DecisionTape` (signals, entries, exits, reason codes)
- `OrderTape` (submitted orders + ids)
- `FillTape` (**must include `slippage_realized_ticks`**)
- `HealthTape` (RAM/CPU/latency/gateway uptime)

### 4.2 No live inference in the execution path (default)

LLM outputs are non‑deterministic (GPU rounding + async timing):

- If LLM is used: generate features offline → store in `InferenceTape`
- Backtests read `InferenceTape`; they do not call Ollama/APIs
- Live may consume **precomputed features only**

### 4.3 Async ordering must be pinned

The engine must operate on a **single ordered event stream**:

`(sequence_id, timestamp, event_type, payload)`

- Backtest/replay drives the engine via this stream
- Live records the stream so it can be replayed

---

## 5) Safety Overlay (Fail‑Closed)

Safety is an enforcement layer. It throws/halts; it does not “warn.”

### 5.1 Risk definitions (must be implemented exactly)

- **Planned risk** = `stop_points * point_value * qty`
- **Buffer risk** = `slippage_buffer_ticks * tick_value * qty`
- **Total planned** = planned + buffer **<= $40**
- **Realized risk** includes slippage + fees
- Any violation: **pause trading (sticky)** + alert

### 5.2 Slippage buffer required

- Default `slippage_buffer_ticks = 4`
- If required stop would exceed max after buffer: **do not trade**

### 5.3 Bracket Orders are mandatory in live

Every live entry must place **server‑side** stop + target (OCO bracket).

If adapter cannot guarantee server-side bracket: **no live, ever**.

### 5.4 Disconnect behavior (correct)

On disconnect:

- Stop submitting new orders immediately
- Rely on existing server-side brackets for protection
- Attempt reconnect → reconcile positions
- If reconnect fails beyond timeout: alert operator; system remains paused

### 5.5 Flattening (Widowmaker Fix — CLOSE then CANCEL)

When a flatten is issued (time-of-day or emergency):

1. **Close position first** (Market or Aggressive Limit) while protection still exists.
2. Verify `position == 0`.
3. **Cancel ALL remaining resting orders** (stops/targets/limits).
4. Verify `open_orders == 0`.

**Race condition note:** Close can coincide with stop triggering → double‑fill reversal.
Mitigation is mandatory: verification loop + fallback ladder. If reversal detected, auto-close up to N attempts, then alert + fail-closed.

### 5.6 Ghost‑position detection (must exist)

Continuously reconcile:

- `local_position_state` vs `broker_reported_position`

If mismatch:

- Freeze new entries immediately
- Alert operator
- Optional: if exposure above threshold, auto‑close

### 5.7 Churn guard (commission death spiral)

Must include:

- max trades/day
- cooldown after stop
- minimum time between entries

---

## 6) Progressive Profiling

We start with a minimal `seed_profile.yaml`. Everything else is progressive.

### 6.1 What can be inferred safely (Derived/Observed)

Allowed derived/observed fields (must carry confidence + provenance pointers):

- `slippage_model_params` (mean/std by regime)
- `latency_profile` (tick→ack ms distribution)
- `avg_commission_per_contract`
- `fill_quality_score`

### 6.2 What must be explicit permission (Never infer)

- Live trading enablement
- Broker linking / credentials
- Instrument expansion (MES → others)
- News trading permissions & blackout rules

---

## 7) News/Event Fusion (Reproducible)

- Live: ingest events → normalize → write `EventTape`
- Replay: read `EventTape` only (no internet)

Economic calendar is required for blackout enforcement, but must be record/replay.

---

## 8) Evidence Chain (Detached Manifest Signature)

**Certificate inside a zip cannot bind to the zip’s hash without circularity.**

Required approach:

1. `evidence/` directory with tapes/logs/configs
2. `manifest.json` = hash of each file in `evidence/`
3. `certificate.json` references `manifest_sha256` (+ signature)
4. Zip payload + manifest + certificate (+ signature)

Verifier:

- unzip
- hash payload → compare to manifest
- verify signature binds manifest

---

## 9) Workflows / Commands (Operator‑First)

### 9.1 One‑True‑Command (verification)

Repo should expose one command that:

- runs tests
- forges artifacts
- verifies strict mode
- verifies evidence hashes & ledger bindings

(Exact command name is repo-defined; keep it stable and document it.)

### 9.2 Definition of Done (DoD)

A task is DONE only if:

- code changes + tests added
- artifacts forged
- verification passes in strict mode
- evidence updated (tapes/logs)
- hostile-audit checklist updated

---

## 10) Promotion Ladder (Gated)

### Stage 0 — Research Skeleton
- deterministic MarketTape ingestion exists
- simple strategy runs on historical tapes

### Stage 1 — Deterministic Backtest
- record/replay yields identical outputs
- evidence package includes tapes + manifests

### Stage 2 — Paper Execution
- ExecutionAdapter implemented for chosen broker simulator/paper
- reconciliation + ghost detection works
- bracket semantics proven (paper‑equivalent acceptable)

### Stage 3 — Micro‑Live (1 contract, strict caps)
- server-side brackets guaranteed
- safety overlay enforced
- daily loss cap enforced
- health monitor enforced

### Stage 4 — Optional Branches (NOT assumed)
- Branch A: personal multi‑asset expansion (IBKR etc.)
- Branch B: futures prop connectivity (Rithmic/CQG)
Core engine unchanged; only adapters/config change.

---

## 11) Module Targets (Repo Locations)

Current repo root: `antigravity_harness/`

Minimum modules (reference implementation exists):

- `antigravity_harness/execution/adapter_base.py`
- `antigravity_harness/execution/safety.py`
- `antigravity_harness/execution/fill_tape.py`
- `antigravity_harness/execution/flatten_manager.py`
- `antigravity_harness/execution/rollover.py`
- `antigravity_harness/execution/sim_adapter.py`
- `antigravity_harness/instruments/mes.py`
- `antigravity_harness/strategies/v050_base_intent.py`
- `tests/test_execution_safety.py`

Adapters (IBKR/Rithmic/etc.) are **optional PRs** and must live under `execution/adapters/`.

---

## 12) Blocking Questions (max 3)

To proceed beyond deterministic research:

1. Which broker first for **paper execution** (IBKR / Tradovate / other)?
2. Which market data source first for MES bars (broker feed vs paid vendor)?
3. Where will the bot run during paper/live (local machine vs VPS)?

If unanswered: continue building broker‑agnostic interfaces + deterministic tapes only.
