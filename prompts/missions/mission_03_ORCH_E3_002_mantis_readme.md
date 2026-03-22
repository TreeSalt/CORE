# Mission: 03_ORCH_E3_002_mantis_readme

## Domain
03_ORCHESTRATION

## Model Tier
Sprint (9b)

## Description
Create a README.md for the MANTIS private repository.

MANTIS = Market Analysis and Neural Trading Intelligence System

REQUIREMENTS:
1. Header with MANTIS name and one-line tagline
2. Architecture: mantis_core execution engine, strategy_zoo, data pipeline, risk management
3. Relationship to CORE: uses core-sdk as git submodule for governance
4. Getting started: clone, install core-sdk, set ALPACA env vars, run paper trading
5. Strategy workflow: generate, backtest, walk-forward validate, paper trade, go live
6. Risk section: position sizing by regime, drawdown limits, walk-forward requirement
7. Do NOT include any API keys or credentials

OUTPUT: mantis_config/README.md
TEST: Assert contains MANTIS header and core-sdk mention
