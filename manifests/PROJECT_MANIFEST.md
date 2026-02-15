# 📟 ANTIGRAVITY: INSTITUTIONAL PROJECT MANIFEST (v2.2)

> **"Ad Astra Per Aspera" — To the stars through difficulties.**

## 💠 Core Architecture
The Antigravity system is a deterministic, event-driven backtesting and validation harness designed to detect genuine trading alpha while ruthlessly discarding overfitted patterns.

### 📁 Unified File System
| Index | Component | Purpose |
| :--- | :--- | :--- |
| **00** | **CORE_MANIFEST** | Version logs, institutional manifests, and iteration history. |
| **01** | **ENGINE** | The the `antigravity_harness` source code and physics core. |
| **02** | **STRATEGIES** | Production and R&D strategy logical definitions. |
| **03** | **CALIBRATION** | YAML grid specifications for multi-dimensional sweeps. |
| **04** | **REPORTS** | Finalized robustness audits, heatmaps, and pass certificates. |
| **05** | **DATA_CACHE** | Persistent OHLCV storage for auditability and speed. |
| **99** | **ARCHIVE** | Historical data, legacy code, and previous phase deliverables. |

## 🛠️ Logic & Validation Gates
Every candidate strategy must pass Eight Institutional Gates:
1.  **GATE0**: Statistical Significance (>40 trades).
2.  **GATE1**: Graveyard Survival (TLT, PFE, ARKK safety).
3.  **GATE2**: Ablation Purity (Redundant indicators = FAIL).
4.  **GATE3**: Profile Metrics (Equity Fortress vs Crypto Profit).
5.  **GATE4**: Gap Stress (NVDA 2015-2024 stress test).
6.  **GATE5**: Time-Split Walk-Forward (OOS Validation).
7.  **GATE6**: Turnover Control (Minimum Hold / Cooldown adherence).
8.  **GATE7**: Robustness Audit (Trade Contribution < 20%).

## 🚀 Execution Standard
The primary interface is `run.py` at the project root:
- `python run.py calibrate`: Full dynamic N-dimensional grid sweep.
- `python run.py validate`: Quick validation of a single parameter set.
- `python run.py emit-signals`: Generate production JSON signals for live bridge.

## 🛡️ Gate Profiles
- **equity_fortress** (Default): Strict Sharpe > 0.5, Low Drawdown.
- **crypto_profit**: High Profit Factor > 1.6, Relaxed Drawdown (<25%).

---
**Build Date**: 2026-02-06
**Status**: **OPERATIONAL**
**Latest Milestone**: Phase 6 Schema Lock & Profit Bridge
