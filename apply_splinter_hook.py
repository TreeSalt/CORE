#!/usr/bin/env python3
"""
apply_splinter_hook.py — Wire Makefile Splinter Hook
DECISION-SOVEREIGN-003 follow-through.
Inserts the 3-line splinter hook before the TRADER_OPS_PROMPT_ID check
in the build target recipe. Permanently kills Gate 5 version chase.
"""
from pathlib import Path

MAKEFILE = Path("Makefile")

# The anchor — first line of the build recipe
ANCHOR = '\t@if [ -z "$(TRADER_OPS_PROMPT_ID)" ]; then \\'

# The 3-line splinter hook (TAB-indented as required by make)
HOOK = (
    '\t@echo "🧬 Splinter Agent: ensuring prompt file exists for v$(VERSION)..."\n'
    '\t@$(VENV_PYTHON) scripts/amend_prompt_version.py --version $(VERSION) 2>&1 | tail -5\n'
    '\t@git add prompts/missions/TRADER_OPS_MASTER_IDE_REQUEST_v$(VERSION).txt 2>/dev/null || true\n'
)

content = MAKEFILE.read_text()

if "Splinter Agent" in content:
    print("✅ Splinter hook already present — nothing to do.")
elif ANCHOR not in content:
    print("❌ Anchor line not found in Makefile. Paste grep output:")
    print("   grep -n 'TRADER_OPS_PROMPT_ID' Makefile")
else:
    patched = content.replace(ANCHOR, HOOK + ANCHOR)
    MAKEFILE.write_text(patched)
    print("✅ Splinter hook inserted.")
    # Verify
    result = [l for l in MAKEFILE.read_text().splitlines() if "Splinter Agent" in l]
    if result:
        print(f"✅ Verified: '{result[0].strip()}'")
    else:
        print("❌ Verification failed — check Makefile manually.")
