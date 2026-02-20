SHELL := /bin/bash
PYTHON := python3
PIP := pip3

DIST ?= dist
VERSION ?= $(shell $(PYTHON) -c "import pathlib,re; p=pathlib.Path('antigravity_harness/__init__.py'); txt=p.read_text(encoding='utf-8') if p.exists() else ''; m=re.search(r'__version__\s*=\s*\"(\d+\.\d+\.\d+)\"', txt); print(m.group(1) if m else '0.0.0')" )

DROP ?= $(DIST)/TRADER_OPS_READY_TO_DROP_v$(VERSION).zip
LEDGER ?= $(DIST)/RUN_LEDGER_v$(VERSION).json
DROP_SHA ?= $(DIST)/DROP_PACKET_SHA256_v$(VERSION).txt
ONE_TRUE := scripts/one_true_command.sh

# Fiduciary Dataset Enforcement
TRADER_OPS_DATASET ?= synthetic
export TRADER_OPS_DATASET

.PHONY: help install lint format type-check test test-hardening preflight clean forge build all heal commands
help:
	@echo ""
	@echo "🐉 TRADER_OPS — Antigravity Harness (v$(VERSION))"
	@echo "═══════════════════════════════════════════════════"
	@echo ""
	@echo "  🔧 CORE"
	@echo "    make install          Install dependencies"
	@echo "    make all              Full pipeline: heal → lint → test → build → verify"
	@echo "    make heal             Proactively repair project (Self-Healing)"
	@echo "    make release          clean → build → verify (Council delivery)"
	@echo ""
	@echo "  🔍 QUALITY"
	@echo "    make lint             Run Ruff linter"
	@echo "    make format           Auto-format code with Ruff"
	@echo "    make type-check       Run Mypy static analysis"
	@echo "    make test             Run all pytest suites"
	@echo "    make test-hardening   Run Phase 9E hardening tests"
	@echo "    make preflight        Run comprehensive pre-flight checks"
	@echo ""
	@echo "  📦 BUILD"
	@echo "    make build            Build strict, self-verifying drop packet → ./dist"
	@echo "    make forge            Forge evidence artifacts"
	@echo ""
	@echo "  🛡️  VERIFICATION"
	@echo "    make verify           Full Sovereign Audit (fail-closed)"
	@echo "    make autopilot-verify Audit latest build artifacts (unified)"
	@echo "    make autopilot-paper  Run strategy in paper mode (guarded)"
	@echo "    make audit            One True Command (Council audit)"
	@echo "    make council-brief    Generate council packet summary"
	@echo "    make audit-fast       Quick hash + verify"
	@echo "    make hashes           Show SHA-256 hashes of dist artifacts"
	@echo "    make zip-verify       Run zip integrity verifier"
	@echo "    make cert-verify      Verify fiduciary certificate"
	@echo "    make show-dist        List dist directory contents"
	@echo ""
	@echo "  🐒 CHAOS (Stress Testing)"
	@echo "    make chaos            Full Chaos Monkey sweep"
	@echo "    make hydra            Hydra vector attack"
	@echo "    make basilisk         Basilisk perfect-forgery attack"
	@echo "    make echo             Echo mix-and-match swap"
	@echo "    make chimera          Chimera stowaway injection"
	@echo "    make kraken           Kraken ensemble desync"
	@echo "    make mimic            Mimic filename evasion"
	@echo "    make legion           Legion statistical evasion"
	@echo "    make gorgon           Gorgon verifier hijack"
	@echo "    make shadow-verify    Shadow runner (full chaos + verify)"
	@echo ""
	@echo "  🩺 ERROR LOG"
	@echo "    make show-errors      Show recent errors (human-friendly)"
	@echo ""
	@echo "  🧹 MAINTENANCE"
	@echo "    make clean            Clean repo artifacts and caches"
	@echo "    make clean-zombies    Kill orphaned simulation processes"
	@echo "    make help             Show this help menu"
	@echo "    make commands         Full command cheat-sheet"
	@echo ""
	@echo "  📖 Full guide: docs/COMMANDS.md"
	@echo ""

commands:
	@echo ""
	@echo "┌─────────────────────────────────────────────────────────────────────┐"
	@echo "│  🐉 TRADER_OPS COMMAND CONSOLE — v$(VERSION)                        │"
	@echo "├─────────────────────────────────────────────────────────────────────┤"
	@echo "│                                                                     │"
	@echo "│  🚀 DAILY WORKFLOW (just do these)                                  │"
	@echo "│    make install ····· Install deps          (first time / update)    │"
	@echo "│    make heal ········ Auto-repair everything (version, hygiene)      │"
	@echo "│    make all ········· Full pipeline          (the one command)       │"
	@echo "│    make release ····· Council delivery       (clean → build → seal)  │"
	@echo "│                                                                     │"
	@echo "│  🔍 QUALITY                 📦 BUILD                                │"
	@echo "│    make lint              make build  (→ dist/)                      │"
	@echo "│    make format            make forge  (evidence)                     │"
	@echo "│    make type-check        make council-brief                         │"
	@echo "│    make test                                                         │"
	@echo "│    make test-hardening    🛡️  VERIFY                                │"
	@echo "│    make preflight         make autopilot-verify (Unified)            │"
	@echo "│                           make autopilot-paper (Guarded)             │"
	@echo "│                           make verify (Sovereign Audit)              │"
	@echo "│                                                                     │"
	@echo "│  🐒 CHAOS                  🧹 MAINTENANCE                           │"
	@echo "│    make chaos (all)       make clean                                │"
	@echo "│    make hydra             make clean-zombies                        │"
	@echo "│    make basilisk          make show-errors                          │"
	@echo "│    make echo / chimera                                              │"
	@echo "│    make kraken / mimic    🔬 CLI MODULE                              │"
	@echo "│    make legion / gorgon   python3 -m antigravity_harness.cli -h     │"
	@echo "│    make shadow-verify     python3 -m antigravity_harness.cli info   │"
	@echo "│                                                                     │"
	@echo "├─────────────────────────────────────────────────────────────────────┤"
	@echo "│  📖 Full guide with examples: docs/COMMANDS.md                      │"
	@echo "│  🩺 Recent errors: make show-errors                                 │"
	@echo "│  💡 Any command -h for details                                      │"
	@echo "└─────────────────────────────────────────────────────────────────────┘"
	@echo ""

show-errors:
	@$(PYTHON) -B scripts/archivist.py --show

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
	$(PYTHON) -B scripts/preflight.py --heal --qa --auto-clean

heal:
	$(PYTHON) -B scripts/self_heal.py --fix

clean:
	$(PYTHON) -B scripts/clean_repo.py --clean --clean-generated

forge:
	$(PYTHON) -B scripts/forge_evidence.py

build:
	STRICT_MODE=1 $(PYTHON) -B scripts/make_drop_packet.py --out-dir dist

# Council-Grade Verification Targets
DIST ?= dist
ONE_TRUE := scripts/one_true_command.sh

.PHONY: audit audit-fast hashes zip-verify cert-verify show-dist

audit:  ## The one word the Council should run
	@mkdir -p "$(DIST)"
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

cert_verify:
	@if [ -f scripts/verify_certificate.py ]; then \
		$(PYTHON) scripts/verify_certificate.py --strict --evidence "$(DIST)"/TRADER_OPS_EVIDENCE_v$(VERSION).zip --trusted-pubkey keys/sovereign.pub; \
	else \
		echo "No scripts/verify_certificate.py present — skipping."; \
	fi

audit-fast: hashes verify
	@echo "✅ audit-fast complete"

show-dist:
	@echo "DIST=$(DIST)"
	@ls -lah "$(DIST)" || true

# Autopilot & Safety Targets
STRATEGY ?= v080_volatility_guard_trend
PROFILE ?= profiles/seed_profile.yaml

autopilot-verify:
	$(PYTHON) scripts/autopilot_supervisor.py verify --dist $(DIST)

autopilot-paper:
	$(PYTHON) scripts/autopilot_supervisor.py run-paper --strategy $(STRATEGY) --profile $(PROFILE) --dist $(DIST)

council-brief:
	$(PYTHON) scripts/council_packet.py

verify:
	@mkdir -p "$(DIST)"
	@test -f "$(ONE_TRUE)" || (echo "Missing $(ONE_TRUE). Create it first." && exit 1)
	@bash "$(ONE_TRUE)" "$(DIST)"
	$(PYTHON) scripts/verify_run_ledger_signature.py --strict --trusted-pubkey keys/sovereign.pub --run-ledger "$(DIST)"/RUN_LEDGER_v$(VERSION).json
	$(PYTHON) scripts/check_dependency_cycles.py
	@echo "🛡️  Fiduciary Verified (Strict): $(shell date)"

clean-zombies:
	@echo "🧹 Cleaning Orphaned Simulations..."
	@pkill -f "antigravity_harness.cli" || true
	@rm -rf state/wal.db-journal || true

release: clean build verify
	@echo "🔥 Institutional Gold Certification Secured: v$$(ls -1t dist/TRADER_OPS_READY_TO_DROP_v*.zip | head -n 1 | sed -E 's/.*_v([0-9]+\.[0-9]+\.[0-9]+)\.zip/\1/')"

all: preflight
	$(MAKE) release SKIP_VERSION_BUMP=1

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
