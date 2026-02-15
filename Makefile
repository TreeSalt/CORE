SHELL := /bin/bash
PYTHON := python3
PIP := pip3

DIST ?= dist
VERSION ?= $(shell $(PYTHON) -c "import pathlib,re; p=pathlib.Path('antigravity_harness/__init__.py'); txt=p.read_text(encoding='utf-8') if p.exists() else ''; m=re.search(r'__version__\s*=\s*\"(\d+\.\d+\.\d+)\"', txt); print(m.group(1) if m else '0.0.0')" )

DROP ?= $(DIST)/TRADER_OPS_READY_TO_DROP_v$(VERSION).zip
LEDGER ?= $(DIST)/RUN_LEDGER_v$(VERSION).json
DROP_SHA ?= $(DIST)/DROP_PACKET_SHA256_v$(VERSION).txt
ONE_TRUE := scripts/one_true_command.sh

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
	@echo "  make build          Build a strict, self-verifying drop packet into ./dist"
	@echo "  make verify         Run the Sovereign Audit against ./dist (fail-closed)"
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
	STRICT_MODE=1 $(PYTHON) -B scripts/make_drop_packet.py --out-dir dist
	@# One-line rule for Sidecar Sovereignty (User Mandate)
	@cd dist && DROP=$$(ls -1t TRADER_OPS_READY_TO_DROP_v*.zip | head -n 1) && sha256sum "$$DROP" > DROP_PACKET_SHA256.txt

# Council-Grade Verification Targets
DIST ?= dist
ONE_TRUE := scripts/one_true_command.sh

.PHONY: audit audit-fast hashes zip-verify cert-verify show-dist

audit:  ## The one word the Council should run
	@test -f "$(ONE_TRUE)" || (echo "Missing $(ONE_TRUE). Create it first." && exit 1)
	@bash "$(ONE_TRUE)" "$(DIST)"

hashes:
	@test -d "$(DIST)" || (echo "Missing dist dir: $(DIST)" && exit 1)
	@echo "== sha256s in $(DIST) =="
	@ls -1 "$(DIST)"/TRADER_OPS_CODE_v*.zip "$(DIST)"/TRADER_OPS_EVIDENCE_v*.zip "$(DIST)"/TRADER_OPS_READY_TO_DROP_v*.zip 2>/dev/null | sort -V | while read -r f; do \
		sha256sum "$$f"; \
	done

zip-verify:
	@test -f scripts/zip_verifier.py || (echo "Missing scripts/zip_verifier.py" && exit 1)
	@$(PYTHON) scripts/zip_verifier.py

cert-verify:
	@if [ -f scripts/verify_certificate.py ]; then \
		$(PYTHON) scripts/verify_certificate.py; \
	else \
		echo "No scripts/verify_certificate.py present — skipping."; \
	fi

audit-fast: hashes verify
	@echo "✅ audit-fast complete"

show-dist:
	@echo "DIST=$(DIST)"
	@ls -lah "$(DIST)" || true

verify:
	@test -f "$(ONE_TRUE)" || (echo "Missing $(ONE_TRUE). Create it first." && exit 1)
	@bash "$(ONE_TRUE)" "$(DIST)"
	$(PYTHON) scripts/check_dependency_cycles.py
	@echo "🛡️  Fiduciary Verified: $(shell date)"

clean-zombies:
	@echo "🧹 Cleaning Orphaned Simulations..."
	@pkill -f "antigravity_harness.cli" || true
	@rm -rf state/wal.db-journal || true

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
