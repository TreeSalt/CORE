# Mission: 03_ORCH_E3_001_gitignore_mantis

## Domain
03_ORCHESTRATION

## Model Tier
Sprint (9b)

## Description
Create a MANTIS-specific .gitignore for the proprietary trading repository.

REQUIREMENTS:
1. Ignore Python artifacts: __pycache__, *.pyc, *.egg-info, dist/, build/
2. Ignore virtual environments: .venv, venv, env
3. Ignore IDE files: .vscode, .idea
4. Ignore ALL key files: *.key, *.pem
5. Ignore market data cache: data/crypto/*.csv
6. Ignore IBKR credentials and session files
7. Ignore OS files: .DS_Store, Thumbs.db
8. Ignore environment files with secrets: .env, *.env
9. Comment header explaining each section

OUTPUT: mantis_config/.gitignore
TEST: Assert file contains *.key and __pycache__ and .venv
