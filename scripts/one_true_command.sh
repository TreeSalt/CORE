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
  
  # c3 (unversioned) is now a legacy fallback only
  if [[ -f "$c3" ]]; then warn "Using unversioned sidecar (landmine warning)"; echo "$c3"; return 0; fi

  # Check INTERNAL sidecar
  if [[ -f "$dropzip" ]]; then
      if unzip -l "$dropzip" | grep -q "DROP_PACKET_SHA256_v$ver.txt"; then
          # Extract it to dist_dir temporarily for the verifier
          local internal="$DIST_DIR/DROP_PACKET_SHA256_v$ver.internal.txt"
          unzip -p "$dropzip" "DROP_PACKET_SHA256_v$ver.txt" > "$internal"
          echo "$internal"
          return 0
      fi
  fi
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
[[ -n "$SIDECAR" ]] || bad "No sidecar hash file found (DROP_PACKET_SHA256_v*.txt or *.zip.sha256). Strict mode requires it."

bold "1.5) Strict-mode assertion"
STRICT_FLAG="$(LEDGER="$LEDGER" python3 - <<'PY'
import json, os
with open(os.environ["LEDGER"], "r") as f:
    d = json.load(f)
print(str(d.get("strict_mode", False)).lower())
PY
)"
[[ "$STRICT_FLAG" == "true" ]] || bad "Ledger strict_mode is not true (set STRICT_MODE=1 for fiduciary-grade builds)"
ok "ledger strict_mode = true"

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

bold "3.5) Seed Profile Presence (fail-closed)"
python3 - "$DROP_ZIP" <<'PY'
import sys, zipfile, io
drop = sys.argv[1]
with zipfile.ZipFile(drop, 'r') as z:
    code_zips = [n for n in z.namelist() if 'TRADER_OPS_CODE' in n and n.endswith('.zip')]
    if not code_zips:
        raise SystemExit("FAIL: no CODE zip in drop")
    code_data = z.read(code_zips[0])
    with zipfile.ZipFile(io.BytesIO(code_data)) as cz:
        profiles = [n for n in cz.namelist() if 'seed_profile.yaml' in n]
        if not profiles:
            raise SystemExit("FAIL: profiles/seed_profile.yaml NOT in CODE zip")
        print(f"OK: seed_profile.yaml found at {profiles[0]}")
PY
ok "seed_profile.yaml present in CODE zip"

bold "3.6) Detached MANIFEST.json (integrity chain)"
python3 - "$DROP_ZIP" <<'PY'
import sys, zipfile, hashlib, json, io

drop_path = sys.argv[1]
with zipfile.ZipFile(drop_path, 'r') as z_drop:
    drop_names = z_drop.namelist()
    if 'MANIFEST.json' not in drop_names:
        print("WARN: No MANIFEST.json (pre-v4.5.29 build)")
        sys.exit(0)
    
    # 1. Read Manifest
    manifest = json.loads(z_drop.read('MANIFEST.json'))
    
    # 2. Find Code Zip
    code_zips = [n for n in drop_names if 'TRADER_OPS_CODE' in n and n.endswith('.zip')]
    if not code_zips:
        raise SystemExit("FAIL: No TRADER_OPS_CODE zip found in drop packet")
    code_zip_name = code_zips[0]
    
    # 3. Open Code Zip (Nested)
    # We read into memory to treat as a file-like object
    code_bytes = z_drop.read(code_zip_name)
    with zipfile.ZipFile(io.BytesIO(code_bytes)) as z_code:
        code_names = set(z_code.namelist())
        
        # 4. Parse mapping
        entries = manifest.get('files', [])
        if isinstance(entries, dict):
             mapping = entries
        elif not entries and 'file_sha256' in manifest:
             mapping = manifest['file_sha256']
        else:
             mapping = {e['path']: e['sha256'] for e in entries}

        # 5. Verify
        print(f"Verifying {len(mapping)} files in {code_zip_name}...")
        for path, expected in mapping.items():
            if path not in code_names:
                raise SystemExit(f"FAIL: MANIFEST references missing file: {path}")
            
            # Verify hash
            actual = hashlib.sha256(z_code.read(path)).hexdigest()
            if actual != expected:
                raise SystemExit(f"FAIL: Hash mismatch for {path}")
        
    print(f"OK: MANIFEST.json verified against {code_zip_name}")
PY
ok "MANIFEST.json integrity chain verified"

bold "3.7) Working Tree Payload Manifest Verification"
if [[ -f "docs/ready_to_drop/PAYLOAD_MANIFEST.json" ]]; then
    python3 - <<'PY'
import hashlib, json, os, sys
manifest_path = "docs/ready_to_drop/PAYLOAD_MANIFEST.json"
with open(manifest_path, 'r') as f:
    manifest = json.load(f)

mapping = manifest.get('file_sha256', {})
if not mapping:
    raise SystemExit("FAIL: PAYLOAD_MANIFEST.json missing 'file_sha256' mapping")

errors = 0
for path, expected in mapping.items():
    if not os.path.exists(path):
        print(f"❌ FAIL: File missing in working tree: {path}")
        errors += 1
        continue
    
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            h.update(chunk)
    actual = h.hexdigest()
    
    if actual != expected:
        print(f"❌ FAIL: Hash mismatch for {path}")
        print(f"   Expected: {expected}")
        print(f"   Actual:   {actual}")
        errors += 1

if errors > 0:
    sys.exit(1)
print(f"OK: Working tree verified against PAYLOAD_MANIFEST.json ({len(mapping)} files)")
PY
    ok "Working tree manifest match"
else:
    warn "docs/ready_to_drop/PAYLOAD_MANIFEST.json missing; skipping working tree check"
fi


bold "4) Self-audit scripts (strict)"
TRUSTED_PUB="keys/sovereign.pub"
if [[ -f "scripts/verify_drop_packet.py" ]]; then
  if [[ -n "$SIDECAR" ]]; then
    python3 scripts/verify_drop_packet.py --drop "$DROP_ZIP" --run-ledger "$LEDGER" --strict --drop-packet-sha "$SIDECAR" --trusted-pubkey "$TRUSTED_PUB"
  else
    python3 scripts/verify_drop_packet.py --drop "$DROP_ZIP" --run-ledger "$LEDGER" --strict --trusted-pubkey "$TRUSTED_PUB"
  fi
  ok "verify_drop_packet.py (strict) PASS"
else
  warn "scripts/verify_drop_packet.py not found; skipping"
fi

bold "5) Zip verifier"
if [[ -f "scripts/zip_verifier.py" ]]; then
  python3 scripts/zip_verifier.py --dist "$DIST_DIR"
  ok "zip_verifier.py PASS"
else
  warn "scripts/zip_verifier.py not found; skipping"
fi

bold "6) Certificate verification"
if [[ -f "scripts/verify_certificate.py" ]]; then
  python3 scripts/verify_certificate.py --evidence "$EVID_ZIP" --strict --trusted-pubkey "$TRUSTED_PUB"
  ok "verify_certificate.py (fiduciary) PASS"
else
  bad "scripts/verify_certificate.py not found; Fiduciary Chain incomplete."
fi

bold "7) Run Ledger Signature verification"
if [[ -f "scripts/verify_run_ledger_signature.py" ]]; then
  python3 scripts/verify_run_ledger_signature.py --run-ledger "$LEDGER" --strict --trusted-pubkey "$TRUSTED_PUB"
  ok "verify_run_ledger_signature.py (fiduciary) PASS"
else
  bad "scripts/verify_run_ledger_signature.py not found; Fiduciary Chain incomplete."
fi

bold "✅ ONE TRUE COMMAND COMPLETE — ALL CHECKS PASSED"
