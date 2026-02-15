# ANTIGRAVITY ITERATION LOG

This document tracks the evolution of trading strategies within the Antigravity Harness. It serves as an audit trail for "What we tried, Why it failed, and What we learned," ensuring we build towards success and do not repeat failures.

## Phase 1: The Baseline (v032)
*   **Strategy**: `v032_simple` (Mean Reversion)
*   **Logic**: Buy if Close < SMA(200) - 2*ATR. Sell if Close > SMA(200).
*   **Hypothesis**: Basic mean reversion works on SPY.
*   **Outcome**: **FAILURE (Logic)**.
*   **Diagnosis**: "Awake but Incompetent." The strategy generated signals but had a Profit Factor of ~0.00 to 0.54. It fundamentally loses money on SPY (2016-2024).
*   **Artifacts**: `reports/phase2a_exploratory`, `ANTIGRAVITY_PHASE2B_AUDIT.zip`.

## Phase 2: Alpha Prime (v040)
*   **Strategy**: `v040_alpha_prime` (Connors RSI Pullback)
*   **Logic**: Buy if Close > SMA(200) AND RSI(2) < Entry. Exit if RSI(2) > Exit.
*   **Hypothesis**: Adding a Trend Filter and using Short-Term RSI (Connors Logic) fixes the baseline.
*   **Outcome**: **FAILURE (Performance)**.
*   **Diagnosis**: "Mechanically Sound, Financially Flawed." Audit confirmed trade execution (40-130 trades) but PF remained < 0.70. The alpha does not exist in efficiently traded SPY large caps in the modern era.
*   **Artifacts**: `reports/phase2c_alpha`, `debug/audit_results_v040.txt`.

## Phase 3: Trend Pivot (v050)
*   **Strategy**: `v050_trend_momentum` (Trend Following)
*   **Logic**: Buy if Close > SMA(200) AND Close > SMA(20) AND RSI(14) > 55.
*   **Hypothesis**: Pivot from Mean Reversion to Trend Following. SPY is a drift asset.
*   **Outcome**: **MARGINAL SUCCESS (The Grinder)**.
*   **Diagnosis**: "Viable but Slow."
    *   **Audit**: PF 1.45 on valid sample.
    *   **Calibration**: PF 1.10 on strict simulation.
    *   **Status**: `NO_PLATEAU` (due to strict Unicorn Gates), but mechanically validated as net profitable.
*   **Artifacts**: `reports/phase3_trend`, `debug/audit_results_v050.txt`.

## Phase 4: Crypto Alpha (v050)
*   **Strategy**: `v050_trend_momentum` (BTC-USD)
*   **Logic**: Long Only Daily Trend Following.
*   **Outcome**: **SUCCESS (Alpha) / FAILURE (Significance)**.
*   **Diagnosis**: "The Sniper."
    *   **Peak PF**: **6.36** on BTC-USD (2020-2025).
    *   **Status**: `NO_PLATEAU` due to low trade count (n=13).
    *   **Insight**: Trend-following on Daily BTC is extremely potent but infrequent. 
*   **Artifacts**: `reports/phase4_crypto`, `ANTIGRAVITY_PHASE4_CRYPTO_COMPLETE.zip`.

## Phase 5: BIT_UNI_CORE (v060)
*   **Strategy**: `v060_bit_uni_core` (BTC-USD 1H)
*   **Objective**: "Bridge the Gap." Target 40+ trades while maintaining PF > 2.0. 
*   **Outcome**: **RE-ALIGNED (Harmonic Resonance)**.
*   **Diagnosis**: "Frequency without Edge" (1H) vs "Alpha Alpha Resonance" (6H).
    *   **Phase 5.1 (1H)**: PF 0.67 (Noise dominance).
    *   **Phase 5.2 (6H Resonance)**: **SUCCESS**. 
    *   **Result**: PF **2.95**. Robustness audit pass (PF 2.02 with top 2 removed).
*   **Artifacts**: `04_PRODUCTION_REPORTS/`, `99_ARCHIVE/ANTIGRAVITY_PHASE5_RESONANCE.zip`.

## Phase 6: Institutional Polishing (v2.1)
*   **Objective**: Streamline the project for long-term R&D.
*   **Changes**: Unified 00-05 numbering, dynamic info health-check, V2.1 Manifest.
*   **Outcome**: **SYSTEM OPERATIONAL**.
