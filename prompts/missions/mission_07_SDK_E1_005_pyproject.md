# Mission: core-sdk pyproject.toml — Package Configuration

## Domain
07_INTEGRATION

## Model Tier
Heavy (27b)

## Description
Create core_sdk/pyproject.toml for the shared SDK package.

This is a PURE MARKDOWN/CONFIG generation task. Output a valid pyproject.toml file.

REQUIREMENTS:
- name: core-sdk
- version: 1.0.0
- description: Constitutional Orchestration & Ratification Engine — Shared SDK
- author: Alec W. Sanchez
- license: MIT (the SDK is open-source)
- python_requires: >=3.12
- NO dependencies (stdlib only)
- build-system: setuptools
- packages: core_sdk

Also create:
- core_sdk/CONTRIBUTING.md — how to contribute to core-sdk (code standards, PR process, testing requirements)
- core_sdk/SECURITY.md — security policy (how to report vulnerabilities, key rotation policy, no secrets in SDK rule)

OUTPUT: pyproject.toml (in repo root, will be moved to core-sdk repo later)
OUTPUT: CONTRIBUTING.md
OUTPUT: SECURITY.md
TEST: File exists and contains [project] section with name = core-sdk
