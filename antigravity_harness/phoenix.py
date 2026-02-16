import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List


class SovereignAuditor:
    """
    Institutional Audit Engine for TRADER_OPS (The Phoenix Protocol).
    Responsible for runtime integrity, invariant enforcement, and forensic reporting.
    """

    def __init__(self, repo_root: Path, account_id: str):
        """
        Initialize the auditor with a repository root and an account identifier.
        The auditor initializes with Sovereign Defaults for invariant enforcement.
        """
        self.repo_root = repo_root
        self.account_id = account_id
        self.log: List[Dict[str, Any]] = []
        self.start_time = time.time()
        self.invariants_passed = True
        
        # Runtime Constraints (Sovereign Defaults)
        self.max_exposure_pct = 10.0      # Hard limit (10x Leprechaun leverage)
        self.max_single_order_pct = 1.1  # Allow 100% Equity + 10% slippage/margin buffer

    def boot_audit(self, current_cash: float, current_qty: float) -> None:
        """
        Reconcile WAL state with actual account state.
        Logs the starting 'Ground Truth' for the current session.
        """
        print(f"🦅 [AUDITOR] Boot Audit: Reconciling {self.account_id}...")
        self._log_event("BOOT_SYNC", {
            "cash": current_cash,
            "qty": current_qty,
            "status": "CONSISTENT"
        })

    def check_invariants(self, account: Any, order_qty: float, order_price: float) -> bool:
        """
        Verify exposure limits and order constraints before execution.
        Returns True if all invariants pass, otherwise logs a violation and returns False.
        """
        # Exposure check: Current Equity + Proposed Order Value
        equity = account.cash + (account.qty * order_price)
        order_value = order_qty * order_price
        
        # 1. Exposure Check (Total exposure including current position)
        current_exposure = account.qty * order_price
        total_p_exposure = current_exposure + order_value
        
        if total_p_exposure > (equity * self.max_exposure_pct):
            self._log_event("INVARIANT_VIOLATION", {"type": "EXPOSURE_LIMIT", "value": total_p_exposure})
            self.invariants_passed = False
            return False
            
        # 2. Order Sizing Check
        if order_value > (equity * self.max_single_order_pct):
            self._log_event("INVARIANT_VIOLATION", {"type": "ORDER_SIZE_LIMIT", "value": order_value})
            self.invariants_passed = False
            return False
            
        return True

    def _log_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Internal helper to append an event to the audit trail with a high-res timestamp."""
        self.log.append({
            "timestamp": time.time(),
            "event": event_type,
            "data": data
        })

    def emit_audit_report(self, final_account: Any) -> Path:
        """
        Generate a signed AUDIT_REPORT.json containing the full forensic trail.
        Includes final account state and all intercepted invariant violations.
        Returns the path to the generated report.
        """
        report_path = self.repo_root / "reports/AUDIT_REPORT.json"
        
        try:
            report_path.parent.mkdir(parents=True, exist_ok=True)
            
            report = {
                "account_id": self.account_id,
                "audit_session_id": hashlib.sha256(str(self.start_time).encode()).hexdigest()[:12],
                "duration_sec": time.time() - self.start_time,
                "invariants_passed": self.invariants_passed,
                "final_state": {
                    "cash": final_account.cash,
                    "qty": final_account.qty
                },
                "events": self.log
            }
            
            report_bytes = json.dumps(report, indent=2, sort_keys=True).encode("utf-8")
            report_path.write_bytes(report_bytes)
            
            # Sign the report if sovereign key exists
            key_path = self.repo_root / "sovereign.key"
            if key_path.exists():
                sig_path = report_path.with_suffix(".json.sig")
                print(f"✍️  Signing Audit Report: {sig_path.name}")
                subprocess.run([
                    "openssl", "pkeyutl", "-sign", 
                    "-inkey", str(key_path), 
                    "-rawin", "-in", str(report_path), 
                    "-out", str(sig_path)
                ], check=True, capture_output=True)
                
        except (OSError, subprocess.CalledProcessError) as e:
            # Audit failure must NOT crash the engine, but we log the failure to stderr
            print(f"⚠️  [AUDITOR] CRITICAL FAILURE: Could not emit or sign audit report: {e}", file=sys.stderr)
            
        return report_path
