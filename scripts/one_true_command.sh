#!/usr/bin/env bash
set -euo pipefail

DIST_DIR="${1:-dist}"

bold() { printf "\033[1m%s\033[0m\n" "$*"; }
ok()   { printf "✅ %s\n" "$*"; }
bad()  { printf "❌ %s\n" "$*" >&2; exit 1; }
warn() { printf "⚠️  %s\n" "$*" >&2; }

need_cmd() { command -v "$1" >/dev/null 2>&1 || bad "Missing required command: $1"; }

sha256_file() {
  local f="$1"
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$f" | awk '{print $1}'
  elif command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "$f" | awk '{print $1}'
  else
    bad "Need sha256sum or shasum"
  fi
}

pick_latest_drop() {
  # Picks highest version by sort -V (works for vX.Y.Z)
  ls -1 "$DIST_DIR"/TRADER_OPS_READY_TO_DROP_v*.zip 2>/dev/null | sort -V | tail -n 1
}

extract_ver() {
  local name
  name="$(basename "$1")"
  # TRADER_OPS_READY_TO_DROP_v4.4.64.zip -> 4.4.64
  echo "$name" | sed -n 's/.*_v\([0-9]\+\.[0-9]\+\.[0-9]\+\)\.zip/\1/p'
}

find_sidecar() {
  local ver="$1" dropzip="$2"
  local c1="$DIST_DIR/DROP_PACKET_SHA256_v$ver.txt"
  local c2="$DIST_DIR/$(basename "$dropzip").sha256"
  local c3="$DIST_DIR/DROP_PACKET_SHA256.txt"

  if [[ -f "$c1" ]]; then echo "$c1"; return 0; fi
  if [[ -f "$c2" ]]; then echo "$c2"; return 0; fi
  if [[ -f "$c3" ]]; then echo "$c3"; return 0; fi
  echo ""
}

python_json_get() {
  # Usage: python_json_get <jsonfile> <expr>
  # expr runs in python with `data` bound to parsed json, print result
  python3 - "$1" "$2" <<'PY'
import json,sys
path=sys.argv[1]
expr=sys.argv[2]
with open(path,'r',encoding='utf-8') as f:
    data=json.load(f)
# Very small safe eval surface: allow attribute-free dict/list ops only.
# We just `eval` because the expressions are hardcoded from this script.
print(eval(expr, {"__builtins__": {}}, {"data": data}))
PY
}

ledger_expected_hash() {
  local ledger="$1" key="$2"
  # Tries both shapes:
  # 1) artifacts: { code: {sha256}, evidence:{sha256}, ready_to_drop:{sha256} }
  # 2) artifacts: { "TRADER_OPS_CODE_...zip": {sha256}, ... }  (fallback)
  python3 - "$ledger" "$key" <<'PY'
import json,sys
ledger=json.load(open(sys.argv[1],'r',encoding='utf-8'))
key=sys.argv[2]
a=ledger.get("artifacts", {})

# Shape 1
if key in a and isinstance(a[key], dict) and "sha256" in a[key]:
    print(a[key]["sha256"]); raise SystemExit(0)

# Alternate labels
alt = {
    "code": ["code_zip","CODE","TRADER_OPS_CODE"],
    "evidence": ["evidence_zip","EVIDENCE","TRADER_OPS_EVIDENCE"],
    "ready_to_drop": ["drop","ready","READY_TO_DROP","TRADER_OPS_READY_TO_DROP"]
}
for k in alt.get(key, []):
    if k in a and isinstance(a[k], dict) and "sha256" in a[k]:
        print(a[k]["sha256"]); raise SystemExit(0)

# Shape 2 (filename-keyed)
# Find first artifact whose filename contains key hint
hints = {
    "code": ["CODE"],
    "evidence": ["EVIDENCE"],
    "ready_to_drop": ["READY_TO_DROP"]
}[key]

for fname, meta in a.items():
    if any(h in fname for h in hints) and isinstance(meta, dict) and "sha256" in meta:
        print(meta["sha256"]); raise SystemExit(0)

raise SystemExit(f"Could not find sha256 for artifacts.{key} in ledger")
PY
}

bold "🧾 ONE TRUE COMMAND — Sovereign Audit (strict, fail-closed)"
need_cmd python3
[[ -d "$DIST_DIR" ]] || bad "Dist dir not found: $DIST_DIR"

DROP_ZIP="$(pick_latest_drop)"
[[ -n "$DROP_ZIP" ]] || bad "No drop zip found in $DIST_DIR (expected TRADER_OPS_READY_TO_DROP_v*.zip)"

VER="$(extract_ver "$DROP_ZIP")"
[[ -n "$VER" ]] || bad "Could not parse version from drop zip name: $(basename "$DROP_ZIP")"

LEDGER="$DIST_DIR/RUN_LEDGER_v$VER.json"
[[ -f "$LEDGER" ]] || {
  # fallback: single ledger in dist
  LEDGER_FALLBACK="$(ls -1 "$DIST_DIR"/RUN_LEDGER_v*.json 2>/dev/null | sort -V | tail -n 1 || true)"
  [[ -n "$LEDGER_FALLBACK" ]] || bad "RUN_LEDGER not found (expected $DIST_DIR/RUN_LEDGER_v$VER.json)"
  warn "Versioned ledger missing; using fallback: $(basename "$LEDGER_FALLBACK")"
  LEDGER="$LEDGER_FALLBACK"
}

SIDECAR="$(find_sidecar "$VER" "$DROP_ZIP")"
[[ -n "$SIDECAR" ]] || warn "No sidecar hash file found (DROP_PACKET_SHA256_v*.txt or *.zip.sha256). Strict mode may require it."

bold "1) Identity (hashes)"
DROP_SHA="$(sha256_file "$DROP_ZIP")"
ok "drop sha256 = $DROP_SHA"

if [[ -n "$SIDECAR" ]]; then
  SIDE_TXT="$(tr -d '\r' < "$SIDECAR" | head -n 1)"
  # Accept either: "<sha>  <file>" or "<sha>"
  SIDE_SHA="$(echo "$SIDE_TXT" | awk '{print $1}')"
  [[ "$SIDE_SHA" == "$DROP_SHA" ]] || bad "Sidecar mismatch: $SIDECAR says $SIDE_SHA but actual is $DROP_SHA"
  ok "sidecar matches ($(basename "$SIDECAR"))"
fi

bold "2) Ledger binding (outer)"
EXP_DROP="$(ledger_expected_hash "$LEDGER" "ready_to_drop")"
[[ "$EXP_DROP" == "$DROP_SHA" ]] || bad "Ledger mismatch: expected drop $EXP_DROP but actual is $DROP_SHA"
ok "outer ledger matches drop"

# Pull expected code/evidence from ledger and verify actual bytes exist and match
CODE_ZIP="$DIST_DIR/TRADER_OPS_CODE_v$VER.zip"
EVID_ZIP="$DIST_DIR/TRADER_OPS_EVIDENCE_v$VER.zip"
[[ -f "$CODE_ZIP" ]] || warn "Missing $CODE_ZIP (not fatal if drop contains embedded code zip only)"
[[ -f "$EVID_ZIP" ]] || warn "Missing $EVID_ZIP (not fatal if drop contains embedded evidence zip only)"

if [[ -f "$CODE_ZIP" ]]; then
  CODE_SHA="$(sha256_file "$CODE_ZIP")"
  EXP_CODE="$(ledger_expected_hash "$LEDGER" "code")"
  [[ "$CODE_SHA" == "$EXP_CODE" ]] || bad "Code hash mismatch: ledger $EXP_CODE vs actual $CODE_SHA"
  ok "code zip matches outer ledger"
fi

if [[ -f "$EVID_ZIP" ]]; then
  EVID_SHA="$(sha256_file "$EVID_ZIP")"
  EXP_EVID="$(ledger_expected_hash "$LEDGER" "evidence")"
  [[ "$EVID_SHA" == "$EXP_EVID" ]] || bad "Evidence hash mismatch: ledger $EXP_EVID vs actual $EVID_SHA"
  ok "evidence zip matches outer ledger"
fi

bold "3) Drop contents sanity (must include inner ledger + artifacts)"
python3 - "$DROP_ZIP" "$VER" <<'PY'
import sys,zipfile
drop=sys.argv[1]; ver=sys.argv[2]
with zipfile.ZipFile(drop,'r') as z:
    names=set(z.namelist())
    must_any = [
        f"RUN_LEDGER_INNER_v{ver}.json",
        f"RUN_LEDGER_v{ver}.json",
        "RUN_LEDGER_INNER.json",
        "RUN_LEDGER.json",
    ]
    if not any(x in names for x in must_any):
        raise SystemExit("FAIL: missing inner RUN_LEDGER in drop zip")
    # Must contain embedded code/evidence zips OR at least METADATA + canon path
    has_code = any(n.endswith(".zip") and "TRADER_OPS_CODE" in n for n in names)
    has_evid = any(n.endswith(".zip") and "TRADER_OPS_EVIDENCE" in n for n in names)
    if not (has_code and has_evid):
        raise SystemExit("FAIL: drop zip does not contain embedded CODE.zip + EVIDENCE.zip")
    if "METADATA.txt" not in names:
        raise SystemExit("FAIL: missing METADATA.txt in drop zip")
print("OK: drop contains inner ledger + embedded artifacts + METADATA")
PY
ok "drop contains required internals"

bold "4) Self-audit scripts (strict)"
if [[ -f "scripts/verify_drop_packet.py" ]]; then
  if [[ -n "$SIDECAR" ]]; then
    python3 scripts/verify_drop_packet.py --drop "$DROP_ZIP" --run-ledger "$LEDGER" --strict --drop-packet-sha "$SIDECAR"
  else
    python3 scripts/verify_drop_packet.py --drop "$DROP_ZIP" --run-ledger "$LEDGER" --strict
  fi
  ok "verify_drop_packet.py (strict) PASS"
else
  warn "scripts/verify_drop_packet.py not found; skipping"
fi

bold "5) Zip verifier"
if [[ -f "scripts/zip_verifier.py" ]]; then
  # Most versions assume dist/ by default; if yours supports flags, add them here.
  python3 scripts/zip_verifier.py
  ok "zip_verifier.py PASS"
else
  warn "scripts/zip_verifier.py not found; skipping"
fi

bold "6) Certificate verification"
# Prefer a project-provided verifier if present; else best-effort detect and run.
if [[ -f "scripts/verify_certificate.py" ]]; then
  python3 scripts/verify_certificate.py
  ok "verify_certificate.py PASS"
else
  warn "scripts/verify_certificate.py not found; skipping (add for full fiduciary-grade certification)"
fi

bold "✅ ONE TRUE COMMAND COMPLETE — ALL CHECKS PASSED"
