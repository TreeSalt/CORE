SHELL := /bin/bash
PYTHON := python3
PIP := pip3

.PHONY: help install lint format type-check test test-hardening preflight clean forge build all

help:
	@echo "Antigravity Harness Automation"
	@echo "------------------------------"
	@echo "  make install        Install dependencies"
	@echo "  make lint           Run Ruff linter"
	@echo "  make format         Auto-format code with Ruff"
	@echo "  make type-check     Run Mypy static analysis"
	@echo "  make test           Run all pytest suites"
	@echo "  make test-hardening Run Phase 9E hardening tests"
	@echo "  make preflight      Run comprehensive pre-flight checks"
	@echo "  make clean          Clean repository artifacts"
	@echo "  make build          Build drop packet (auto-versioning)"
	@echo "  make all            Run lint, type-check, test, preflight, and build"

install:
	$(PIP) install -r requirements.txt
	$(PIP) install -e . --no-deps

lint:
	$(PYTHON) -m ruff check .

format:
	$(PYTHON) -m ruff check --fix .

type-check:
	$(PYTHON) -m mypy .

test:
	$(PYTHON) -m pytest

test-hardening:
	PYTHONPATH=. $(PYTHON) tests/test_phase_9e_hardening.py

preflight:
	$(PYTHON) -B scripts/verify_imports.py
	$(PYTHON) -B scripts/preflight.py --qa --auto-clean

clean:
	$(PYTHON) -B scripts/clean_repo.py --clean --clean-generated

forge:
	$(PYTHON) -B scripts/forge_evidence.py

build:
	$(PYTHON) -B scripts/make_drop_packet.py --out-dir dist

verify:
	@set -e; \
	DROP=$(shell ls -1t dist/TRADER_OPS_READY_TO_DROP_v*.zip 2>/dev/null | head -n 1); \
	VER=$$(echo $$DROP | sed -E 's/.*_v([0-9]+\.[0-9]+\.[0-9]+)\.zip/\1/'); \
	LEDGER=dist/RUN_LEDGER_v$$VER.json; \
	SIDECAR=dist/DROP_PACKET_SHA256.txt; \
	$(PYTHON) scripts/verify_drop_packet.py --drop "$$DROP" --run-ledger "$$LEDGER" --drop-packet-sha "$$SIDECAR" --strict

release: clean build verify
	@echo "🔥 Institutional Gold Certification Secured: v$$(ls -1t dist/TRADER_OPS_READY_TO_DROP_v*.zip | head -n 1 | sed -E 's/.*_v([0-9]+\.[0-9]+\.[0-9]+)\.zip/\1/')"

all: preflight release

chaos:
	@echo "🐒 Chaos Monkey vs The Dragon..."
	$(PYTHON) scripts/chaos_monkey.py all
	-$(PYTHON) scripts/zip_verifier.py
	@echo "🐒 Chaos Loop Complete."

hydra:
	@echo "🐍 The Hydra vs The Dragon..."
	$(PYTHON) scripts/chaos_monkey.py hydra
	-$(PYTHON) scripts/zip_verifier.py
	@echo "🐍 Hydra Loop Complete."

basilisk:
	@echo "🦎 The Basilisk vs The Dragon..."
	$(PYTHON) scripts/chaos_monkey.py basilisk
	-$(PYTHON) scripts/zip_verifier.py
	@echo "🦎 Basilisk Loop Complete."

echo:
	@echo "👻 The Echo vs The Dragon..."
	$(PYTHON) scripts/chaos_monkey.py echo
	-$(PYTHON) scripts/zip_verifier.py
	@echo "👻 Echo Loop Complete."

chimera:
	@echo "🦁 The Chimera vs The Dragon..."
	$(PYTHON) scripts/chaos_monkey.py chimera
	-$(PYTHON) scripts/zip_verifier.py
	@echo "🦁 Chimera Loop Complete."

kraken:
	@echo "🐙 The Kraken vs The Dragon..."
	$(PYTHON) scripts/chaos_monkey.py kraken
	-$(PYTHON) scripts/zip_verifier.py
	@echo "🐙 Kraken Loop Complete."

mimic:
	@echo "🎭 The Mimic vs The Dragon..."
	$(PYTHON) scripts/chaos_monkey.py mimic
	-$(PYTHON) scripts/zip_verifier.py
	@echo "🎭 Mimic Loop Complete."

legion:
	@echo "👥 The Legion vs The Dragon..."
	$(PYTHON) scripts/chaos_monkey.py legion
	-$(PYTHON) scripts/zip_verifier.py
	@echo "👥 Legion Loop Complete."

gorgon:
	@echo "🐍 The Gorgon vs The Dragon..."
	python3 scripts/chaos_monkey.py gorgon
	python3 scripts/zip_verifier.py
	@echo "🐍 Gorgon Loop Complete."


# Stress & Chaos (Titan Tier Verification)
shadow-verify:
	$(PYTHON) scripts/shadow_runner.py --chaos-mode all
