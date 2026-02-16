# Agentic Onboarding: TRADER_OPS (Cognitive Bridge)

Welcome, Agent. You are assuming control of the **TRADER_OPS Sovereign Protocol**. This document provides the high-fidelity instructions required to verify the current state and resume development without information loss.

---

## 1. Immediate Verification (Audit Gate)

To confirm the integrity of the project you have just inherited, run the institutional preflight suite:

```bash
python3 scripts/preflight.py --auto-clean --qa
```

**Success Criteria**:
- Zero `__pycache__` or `.pyc` files remaining.
- All core imports and paths verified.
- No "Schisms" (version mismatches) detected.

---

## 2. Navigating the Graduation (v4.5.14)

The project has recently undergone an "Institutional Gold" graduation. Key transitions:

1.  **WAL to Phoenix**: Use `antigravity_harness/phoenix.py` for all auditing. The legacy `WriteAheadLog` is deprecated but preserved for contract testing.
2.  **Sovereign Forge**: Use `scripts/make_drop_packet.py` to create releases. It enforces bit-perfect rules and signs artifacts.
3.  **Essence Purity**: Ingestion parsing logic is now internal to `antigravity_harness.essence` to ensure portability.

---

## 3. Core Operational Loop

### 3.1 Strategy Certification
To test if a strategy is "Fiduciary Grade":
```bash
python -m antigravity_harness.cli certify-run \
  --strategy v050_trend_momentum \
  --symbols BTC-USD \
  --timeframes 4h \
  --gate-profile crypto_profit
```

### 3.2 The Final Forge
To produce a shippable "Ready-to-Drop" packet:
```bash
make build
```
Verify the output in `dist/`.

---

## 4. Architectural Entry Points

| Purpose | Entry Point |
| :--- | :--- |
| **Engine Physics** | `antigravity_harness/engine.py` |
| **Auditing/Forensics** | `antigravity_harness/phoenix.py` |
| **Quality Gates** | `antigravity_harness/gates.py` |
| **Intelligence Ingest** | `antigravity_harness/essence.py` |
| **Release Logic** | `antigravity_harness/forge/build.py` |

---

## 5. Security Context (Priority Alpha)

When modifying the codebase:
1.  **Strict Mode**: The forge operates in `STRICT_MODE=1` by default. Do not add untracked files without intending them to be part of the legal release record.
2.  **Determinism**: Avoid `datetime.now()` or non-seeded random numbers. Always use fixed epochs for verification logic.
3.  **Audit Awareness**: Any new critical state transition **MUST** be registered with `engine.auditor.log_event()`.

---

*Transmission Secure. Sovereignty Confirmed.*
